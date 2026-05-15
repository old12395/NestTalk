"""世界书引擎 — 关键词/正则匹配 + 递归触发 + Token 预算控制"""

import re
from typing import Optional
from loguru import logger


class WorldBookEngine:
    """世界书条目匹配与注入引擎"""

    def __init__(self):
        pass

    def scan(
        self,
        entries: dict[str, dict],
        messages: list[dict],
        scan_depth: int = 20,
        max_recursion: int = 3,
        token_budget: int = 1024,
    ) -> list[dict]:
        """
        扫描对话历史，匹配并激活世界书条目。

        Args:
            entries: 世界书条目 {"0": {"keys": [...], "content": "...", "recursive": bool, ...}}
            messages: 对话历史 [{"role": ..., "content": ...}]
            scan_depth: 扫描最近的 N 条消息
            max_recursion: 递归最大深度
            token_budget: Token 预算上限

        Returns:
            激活的条目列表 [{"title": "...", "content": "...", "priority": ...}]
        """
        if not entries:
            return []

        # 提取最近 N 条消息文本
        recent_messages = messages[-scan_depth:] if len(messages) > scan_depth else messages
        combined_text = "\n".join(
            msg.get("content", "") for msg in recent_messages if msg.get("content")
        )

        if not combined_text.strip():
            return []

        # 第一轮：匹配所有条目
        activated_ids = set()
        priority_map = {}  # id → priority

        for entry_id, entry in entries.items():
            if entry.get("disable", False):
                continue

            keys = self._parse_keys(entry.get("keys", []))
            if not keys:
                continue

            matched = self._match_keys(keys, combined_text)
            if matched:
                activated_ids.add(entry_id)
                priority_map[entry_id] = entry.get("order", 0)

        # 递归触发（被激活条目的 content 如果命中其他条目的 key，也激活）
        if max_recursion > 0:
            activated_ids = self._recursive_activate(
                entries, activated_ids, set(), max_recursion, 1
            )

        # 按优先级排序
        activated = []
        for eid in activated_ids:
            entry = entries[eid]
            activated.append({
                "id": eid,
                "title": entry.get("comment", f"条目 {eid}"),
                "content": entry.get("content", ""),
                "priority": priority_map.get(eid, 0),
                "position": entry.get("position", "before_char"),
                "selective": entry.get("selective", False),
            })

        activated.sort(key=lambda x: (x["priority"], x["id"]))

        # Token 预算控制
        activated = self._apply_token_budget(activated, token_budget)

        return activated

    def _parse_keys(self, keys) -> list[str]:
        """解析 keys 字段（支持字符串、列表、逗号分隔）"""
        if isinstance(keys, str):
            return [k.strip() for k in keys.split(",") if k.strip()]
        if isinstance(keys, list):
            return [str(k).strip() for k in keys if str(k).strip()]
        return []

    def _match_keys(self, keys: list[str], text: str) -> bool:
        """检查任意 key 是否在文本中匹配"""
        for key in keys:
            # 尝试正则匹配
            if self._is_regex(key):
                try:
                    if re.search(key, text, re.IGNORECASE):
                        return True
                except re.error:
                    pass

            # 纯文本匹配（忽略大小写）
            if key.lower() in text.lower():
                return True

        return False

    def _is_regex(self, pattern: str) -> bool:
        """检测是否为正则表达式（以 / 包裹）"""
        return pattern.startswith("/") and (pattern.endswith("/") or pattern.endswith("/i"))

    def _recursive_activate(
        self,
        entries: dict,
        activated: set,
        visited: set,
        max_depth: int,
        current_depth: int,
    ) -> set:
        """递归激活：已激活条目 content 命中其他条目的 keys"""
        if current_depth > max_depth:
            return activated

        new_activated = set(activated)

        for eid in activated:
            if eid in visited:
                continue
            visited.add(eid)

            entry = entries.get(eid)
            if not entry or not entry.get("recursive", False):
                continue

            content = entry.get("content", "")
            if not content:
                continue

            for other_id, other_entry in entries.items():
                if other_id in new_activated:
                    continue
                if other_entry.get("disable", False):
                    continue

                keys = self._parse_keys(other_entry.get("keys", []))
                if self._match_keys(keys, content):
                    new_activated.add(other_id)
                    logger.debug(f"🔄 递归激活: {eid} → {other_id}")

        if new_activated != activated:
            return self._recursive_activate(
                entries, new_activated, visited, max_depth, current_depth + 1
            )

        return new_activated

    def _apply_token_budget(self, entries: list[dict], budget: int) -> list[dict]:
        """
        按 Token 预算裁剪条目。

        策略：优先级高的优先保留，低优先级且内容长则裁剪。
        """
        if budget <= 0:
            return entries

        selected = []
        total_chars = 0
        char_budget = budget * 2  # 粗略：中文约 2 字符/token

        for item in entries:
            content_len = len(item.get("content", ""))
            if total_chars + content_len <= char_budget:
                selected.append(item)
                total_chars += content_len
            else:
                # 尝试裁剪内容
                remaining = char_budget - total_chars
                if remaining > 100:  # 至少保留 100 字符
                    truncated = item.copy()
                    truncated["content"] = item["content"][:remaining] + "..."
                    selected.append(truncated)
                break

        return selected

    def format_for_prompt(self, entries: list[dict], position: str = "before_char") -> str:
        """
        将激活的条目格式化为可注入 prompt 的文本。

        Args:
            entries: 激活的条目列表
            position: 注入位置筛选 ("before_char", "after_char", "in_depth", 或 None=全部)

        Returns:
            格式化的文本
        """
        if not entries:
            return ""

        filtered = entries
        if position:
            filtered = [e for e in entries if e.get("position") == position]

        if not filtered:
            return ""

        lines = ["【背景信息】"]
        for e in filtered:
            title = e.get("title", "")
            content = e.get("content", "")
            if title:
                lines.append(f"▸ {title}：{content}")
            else:
                lines.append(f"▸ {content}")
        lines.append("")

        return "\n".join(lines)


# 全局单例
worldbook_engine = WorldBookEngine()
