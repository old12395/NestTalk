"""长期记忆系统 — 向量存储 + RAG 检索 + 用户画像"""

import json
import hashlib
from typing import Optional
from datetime import datetime, timedelta

from loguru import logger

# 延迟导入 ChromaDB（避免未安装时崩溃）
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB 未安装，记忆系统将使用降级模式")


class MemorySystem:
    """
    长期记忆系统。

    架构：
    - ChromaDB 向量存储（语义检索）
    - 记忆条目带重要性评分
    - 记忆衰减机制
    - 用户画像自动提取
    """

    def __init__(self, persist_dir: str = "./data/memory"):
        self.persist_dir = persist_dir
        self.collection = None

        if CHROMA_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                self.collection = self.client.get_or_create_collection(
                    name="long_term_memory",
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"✅ 记忆系统初始化: {persist_dir}")
            except Exception as e:
                logger.error(f"ChromaDB 初始化失败: {e}")
                self.collection = None
        else:
            self.client = None
            self.collection = None
            logger.info("⚠️ 记忆系统运行在降级模式（无向量检索）")

    # ─── 记忆存储 ─────────────────────────────

    def remember(
        self,
        user_id: str,
        content: str,
        importance: float = 1.0,
        tags: Optional[list[str]] = None,
        source_message_id: Optional[str] = None,
    ):
        """
        存储一条记忆。

        Args:
            user_id: 用户 ID
            content: 记忆内容
            importance: 重要性评分 (0-10)
            tags: 标签
            source_message_id: 来源消息 ID
        """
        memory_id = self._gen_id(user_id, content)

        if self.collection:
            try:
                self.collection.upsert(
                    ids=[memory_id],
                    documents=[content],
                    metadatas=[{
                        "user_id": user_id,
                        "importance": importance,
                        "tags": json.dumps(tags or []),
                        "source_message_id": source_message_id or "",
                        "created_at": datetime.utcnow().isoformat(),
                        "last_accessed_at": datetime.utcnow().isoformat(),
                        "access_count": 0,
                    }],
                )
            except Exception as e:
                logger.error(f"存储记忆失败: {e}")

        return memory_id

    def remember_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_reply: str,
        extract_facts: bool = True,
    ):
        """
        从一轮对话中提取并存储记忆。

        Args:
            user_id: 用户 ID
            user_message: 用户说的话
            assistant_reply: 助手回复
            extract_facts: 是否提取事实
        """
        # 存储完整对话轮次
        combined = f"用户说: {user_message}\n角色回复: {assistant_reply}"
        self.remember(user_id, combined, importance=2.0, tags=["conversation"])

        # TODO: 使用 LLM 提取关键事实
        # 例如: "用户喜欢吃川菜" / "用户下周有考试" / "用户的猫叫小橘"
        # 提取的事实重要性更高，标记更精准的 tag

    # ─── 记忆检索 ─────────────────────────────

    def recall(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
        min_importance: float = 0.0,
    ) -> list[dict]:
        """
        检索相关记忆。

        Args:
            user_id: 用户 ID
            query: 查询文本（当前对话内容）
            top_k: 返回条数
            min_importance: 最低重要性阈值

        Returns:
            [{"content": "...", "importance": 1.5, "relevance": 0.95, ...}]
        """
        if not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": user_id},
            )

            memories = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0

                    importance = float(metadata.get("importance", 1.0))
                    if importance < min_importance:
                        continue

                    # 将 cosine distance 转为相似度 (0-1)
                    relevance = max(0, 1 - distance) if distance else 0.8

                    memories.append({
                        "content": doc,
                        "importance": importance,
                        "relevance": round(relevance, 3),
                        "tags": json.loads(metadata.get("tags", "[]")),
                        "created_at": metadata.get("created_at", ""),
                    })

            # 更新访问时间和计数
            if results and results.get("ids") and results["ids"][0]:
                for mem_id in results["ids"][0]:
                    self._touch_memory(mem_id)

            # 按重要性 × 相关性排序
            memories.sort(key=lambda m: m["importance"] * m["relevance"], reverse=True)

            return memories[:top_k]

        except Exception as e:
            logger.error(f"记忆检索失败: {e}")
            return []

    # ─── 记忆格式化 ────────────────────────────

    def format_for_prompt(self, memories: list[dict], max_chars: int = 500) -> str:
        """
        将记忆格式化为可注入 prompt 的文本。

        Args:
            memories: recall() 返回的记忆列表
            max_chars: 最大字符数

        Returns:
            格式化的记忆文本
        """
        if not memories:
            return ""

        lines = []
        total_chars = 0

        for mem in memories:
            content = mem["content"]
            line = f"• {content}"
            if total_chars + len(line) > max_chars:
                break
            lines.append(line)
            total_chars += len(line)

        return "\n".join(lines) if lines else ""

    # ─── 记忆衰减 ─────────────────────────────

    def decay_memories(self, user_id: str, days_threshold: int = 30):
        """
        衰减长期未访问的记忆。

        策略：超过 30 天未访问的记忆，重要性每次衰减 20%。
        重要性低于 0.1 的记忆将被删除。
        """
        if not self.collection:
            return

        cutoff = (datetime.utcnow() - timedelta(days=days_threshold)).isoformat()

        try:
            results = self.collection.get(
                where={"user_id": user_id},
            )

            if not results or not results["ids"]:
                return

            for i, mem_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                last_access = metadata.get("last_accessed_at", "")

                if last_access < cutoff:
                    importance = float(metadata.get("importance", 1.0))
                    new_importance = importance * 0.8

                    if new_importance < 0.1:
                        self.collection.delete(ids=[mem_id])
                        logger.debug(f"🗑️ 删除衰减记忆: {mem_id}")
                    else:
                        self.collection.update(
                            ids=[mem_id],
                            metadatas=[{**metadata, "importance": new_importance}],
                        )

        except Exception as e:
            logger.error(f"记忆衰减失败: {e}")

    # ─── 用户画像 ─────────────────────────────

    def extract_profile(self, user_id: str) -> dict:
        """
        从记忆中提取用户画像。

        TODO: 使用 LLM 从记忆摘要中提取结构化画像
        目前返回基础统计信息。
        """
        if not self.collection:
            return {"user_id": user_id, "facts": [], "memory_count": 0}

        try:
            results = self.collection.get(
                where={"user_id": user_id},
            )

            count = len(results["ids"]) if results and results["ids"] else 0

            return {
                "user_id": user_id,
                "memory_count": count,
                "facts": [],
                "summary": f"已存储 {count} 条记忆",
            }
        except Exception:
            return {"user_id": user_id, "facts": [], "memory_count": 0}

    # ─── 工具方法 ─────────────────────────────

    def _gen_id(self, user_id: str, content: str) -> str:
        """生成记忆唯一 ID"""
        raw = f"{user_id}:{content}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def _touch_memory(self, memory_id: str):
        """更新记忆的访问时间和计数"""
        if not self.collection:
            return
        try:
            result = self.collection.get(ids=[memory_id])
            if result and result["metadatas"]:
                meta = result["metadatas"][0]
                meta["last_accessed_at"] = datetime.utcnow().isoformat()
                meta["access_count"] = int(meta.get("access_count", 0)) + 1
                self.collection.update(ids=[memory_id], metadatas=[meta])
        except Exception:
            pass

    def clear_user_memories(self, user_id: str):
        """清空用户所有记忆"""
        if not self.collection:
            return
        try:
            self.collection.delete(where={"user_id": user_id})
            logger.info(f"清空用户记忆: {user_id}")
        except Exception as e:
            logger.error(f"清空记忆失败: {e}")


# 全局单例
memory_system = MemorySystem()
