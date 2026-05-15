# NestTalk（栖言）设计文档

> 精简版酒馆 × AstrBot 融合体 —— AI 情感陪聊机器人框架
>
> 设计日期：2026-05-15

---

## 一、项目目标

一个兼容酒馆生态（角色卡、世界书、预设）的多平台 AI 情感陪聊机器人，具备真人化陪伴能力：
- 不是问一句答一句，而是有温度、有情感、会主动关心
- 多模态自然交互（文字、图片、语音）
- 跨平台触达（TG、QQ、微信等）
- 简洁直观的后台管理

---

## 二、技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| 后端框架 | Python FastAPI | AI/LLM 生态最全，异步高性能 |
| 数据库 | PostgreSQL | 结构化数据，JSON 支持好 |
| 缓存 | Redis | 会话状态、消息队列、速率限制 |
| 向量数据库 | ChromaDB / Milvus Lite | 长期记忆 RAG，轻量嵌入 |
| 前端 | Vue 3 + Vite + Naive UI | 移动端友好，组件丰富 |
| 部署 | Docker Compose | 一键部署，环境隔离 |

---

## 三、核心模块设计

### 3.1 角色系统（Character）

**兼容标准：**
- Character Card V2（`chara` tEXt chunk）
- Character Card V3（`ccv3` tEXt chunk，base64 编码）
- CHARX 格式（ZIP 包含 `card.json` + assets）
- JSON 裸格式

**支持字段（V3 完整版）：**
```
name, description, personality, scenario, mes_example
first_mes, alternate_greetings, system_prompt
post_history_instructions, creator_notes
character_book (内嵌世界书), extensions, assets
nickname, creator, character_version, spec_version
```

**功能：**
- 导入角色卡（拖拽上传 PNG/CHARX/JSON）
- 角色在线编辑器
- 多角色管理、收藏、分组
- 角色预览（头像 + 基本信息 + 开场白预览）

### 3.2 世界书引擎（WorldBook / Lorebook）

**兼容格式：** SillyTavern lorebook JSON

**条目结构：**
```json
{
  "entries": {
    "0": {
      "keys": ["关键词1", "关键词2"],
      "content": "条目内容",
      "comment": "备注",
      "constant": false,
      "selective": false,
      "order": 0,
      "position": "before_char",
      "disable": false,
      "recursive": true,
      "extensions": {}
    }
  }
}
```

**触发机制：**
- 关键词精确匹配
- 正则表达式匹配
- 向量相似度匹配（可选）
- 递归触发（可配置最大深度）

**注入策略（省 token 核心）：**
- 按条目优先级排序
- Token 预算上限控制
- 扫描深度限制（最近 N 条消息）
- 按需激活（只在相关时注入）

### 3.3 预设系统（Preset）

**模板引擎：**
- Jinja2 风格模板，支持宏变量
- 内置宏：`{{char}}`, `{{user}}`, `{{personality}}`, `{{scenario}}`, `{{description}}`, `{{mes_example}}`

**上下文模板编排：**
- 自定义各模块在 System Prompt 中的位置和顺序
- 支持：角色定义、世界书、对话历史、用户画像、记忆摘要
- 预设可导出/导入分享

**预设结构：**
```json
{
  "name": "预设名称",
  "system_prompt": "你是 {{char}}...",
  "context_template": {
    "order": ["persona", "scenario", "world_book", "history", "memory"],
    "insert_position": {
      "world_book": "before_history",
      "memory": "after_world_book"
    }
  },
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2048,
    "presence_penalty": 0.5,
    "frequency_penalty": 0.3
  }
}
```

### 3.4 LLM 网关

**统一接口：**
- 兼容 OpenAI Chat Completions API 格式
- 所有 LLM 调用经过网关统一管理

**支持模型：**
- OpenAI (GPT-4, GPT-4o, GPT-4o-mini)
- Anthropic Claude
- Google Gemini
- DeepSeek
- 通义千问
- 智谱 GLM
- Ollama 本地模型
- 任何 OpenAI 兼容 API

**功能：**
- 流式输出（SSE）
- 自动 fallback（主模型挂了切备用）
- Token 计数 & 费用统计
- 速率限制
- 请求日志

### 3.5 多模态引擎

**设计原则：用户可自由配置每个多模态能力使用的模型/服务。**

**识图（Vision）：**
- 通过 LLM Vision API（GPT-4o, Gemini, Claude）
- 本地模型（LLaVA 等）
- 配置项：模型、API Key、endpoint

**生图（Image Generation）：**
- DALL-E 3
- Stable Diffusion (API / 本地)
- Midjourney (via API proxy)
- 配置项：模型、尺寸、质量、风格

**语音识别（STT）：**
- OpenAI Whisper API
- 本地 Whisper
- 云服务（Azure / 阿里云）
- 配置项：语言、模型大小

**语音合成（TTS）：**
- OpenAI TTS
- Edge TTS（免费）
- ElevenLabs（高质量）
- 配置项：声音、语速、情感

**调用方式：**
- LLM 在对话中自主决定何时调用（function calling / tool use）
- 例如：用户发图片 → LLM 自动调用 vision → 用识别结果回复
- 例如：角色判断该用语音回复 → LLM 调用 TTS → 发送语音

### 3.6 平台适配器

**设计原则：插件化架构，统一消息协议，新增平台只需实现 Adapter 接口。**

**统一消息协议：**
```json
{
  "platform": "telegram",
  "chat_id": "xxx",
  "user_id": "xxx",
  "message_type": "text | image | voice | video | file",
  "content": "消息内容或文件URL",
  "timestamp": 1234567890,
  "reply_to": null
}
```

**首批支持平台：**
- Telegram Bot API
- QQ（NapCat / LLOneBot）
- 微信（企业微信 / WeChatFerry）

**适配器接口：**
```python
class PlatformAdapter(ABC):
    async def start(self): ...
    async def stop(self): ...
    async def send_message(self, chat_id, content, media=None): ...
    async def on_message(self, callback): ...  # 消息回调
    def get_platform_name(self) -> str: ...
```

### 3.7 记忆系统

**短期记忆：**
- 滑动窗口对话历史（可配置 N 轮）
- 消息自动摘要（超过窗口的压缩为摘要）

**长期记忆（RAG）：**
- 对话自动分段 → 向量嵌入 → ChromaDB 存储
- 新消息到来时检索相关记忆
- 记忆重要性评分（重复提及的加深记忆）
- 记忆衰减机制（久未提及的降低权重）

**用户画像：**
- 自动提取：称呼、年龄、性别、职业、兴趣、偏好
- 语义理解而非关键词匹配
- 画像随时间更新

### 3.8 主动交互引擎 🔥

**核心设计：角色不是应答机器，是有情感温度的陪伴者。**

**触发场景：**

| 类型 | 触发条件 | 示例 |
|------|----------|------|
| 定时问候 | 预设时间点 | 早安 8:00 / 晚安 23:00 |
| 情感驱动 | 情感状态达到阈值 | "今天还没跟你说话呢，有点想你…" |
| 事件驱动 | 外部事件触发 | 生日提醒、节日祝福、天气变化 |
| 话题驱动 | 检测到用户兴趣更新 | "你上次说想看的电影上映了！" |
| 随机闲聊 | 概率触发 | 角色主动分享日常/想法 |

**控制策略：**
- 频率上限（每小时/每天最多主动发言次数）
- 静默时段（夜间不打扰）
- 用户可随时暂停/恢复主动消息
- **情感状态可视化：** 后台面板显示角色当前 mood

### 3.9 后台管理面板 ⭐

**设计原则：**
- 🖥️ PC 端功能完善
- 📱 移动端完全适配（响应式布局，PWA 可选）
- 直观 = 看到就能用，不需要文档

**面板模块：**

```
导航栏
├── 🏠 仪表盘
│   ├── 今日概览（消息数、Token消耗、费用）
│   ├── 活跃角色状态卡片
│   └── 近7天趋势图
│
├── 🎭 角色管理
│   ├── 角色列表（头像缩略图 + 名称 + 标签）
│   ├── 拖拽导入角色卡
│   ├── 角色编辑器
│   └── 批量操作
│
├── 📚 世界书管理
│   ├── 世界书列表
│   ├── 条目编辑器（可视化编辑 + JSON编辑）
│   ├── 关键词测试工具
│   └── 导入/导出
│
├── ⚙️ 预设管理
│   ├── 预设列表
│   ├── 预设编辑器（模板可视化 + 预览）
│   └── 导入/导出
│
├── 💬 对话监控
│   ├── 实时对话流
│   ├── 对话历史查看
│   ├── 干预工具（手动回复/切换角色）
│   └── 会话归档
│
├── 🧠 记忆管理
│   ├── 记忆条目浏览
│   ├── 用户画像查看
│   ├── 记忆手动编辑/删除
│   └── 重置记忆
│
├── 🤖 模型配置
│   ├── LLM 模型列表 & 配置
│   ├── 多模态模型配置（Vision / Image / STT / TTS）
│   ├── 模型测试工具
│   └── Fallback 链配置
│
├── 🔌 平台连接
│   ├── 平台列表及状态
│   ├── Telegram Bot 配置
│   ├── QQ Bot 配置
│   ├── 微信配置
│   └── 连接状态指示灯
│
├── ⏰ 主动交互
│   ├── 定时任务管理
│   ├── 情感状态查看
│   ├── 主动消息频率设置
│   └── 静默时段设置
│
├── 📊 统计分析
│   ├── Token 消耗趋势
│   ├── 费用报表
│   ├── 用户活跃度分析
│   └── 角色使用排行
│
├── 🔒 安全设置
│   ├── 敏感内容过滤开关 & 级别
│   ├── 用户黑白名单
│   └── API 访问控制
│
└── 💾 系统设置
    ├── 全局参数
    ├── 备份与恢复（见 3.10）
    ├── 系统日志
    └── 关于 & 更新
```

**移动端适配要点：**
- 底部 Tab 导航替代侧边栏
- 卡片式布局，单手操作友好
- 表单字段适配移动端输入
- 关键操作支持手势（左滑删除等）
- PWA 支持（可添加到桌面）

### 3.10 数据备份与迁移 ⭐

**设计原则：前瞻性架构，永远向前兼容。**

**导出格式：**
```json
{
  "format": "nesttalk_backup_v1",
  "version": "1.0.0",
  "exported_at": "2026-05-15T12:00:00Z",
  "data": {
    "characters": [...],      // 所有角色
    "world_books": [...],     // 所有世界书
    "presets": [...],         // 所有预设
    "model_configs": {...},   // 模型配置
    "platform_configs": {...},// 平台配置（脱敏）
    "system_settings": {...}, // 系统设置
    "scheduled_tasks": [...], // 定时任务
    "memories": [...]         // 可选：长期记忆数据
  },
  "checksum": "sha256:xxxx"
}
```

**版本兼容策略：**

1. **格式版本化：** 导出文件带有明确的 `version` 字段
2. **向后兼容：** 新版系统必须能导入旧版导出文件
   - 旧字段保留不动
   - 新增字段使用默认值填充
   - 废弃字段导入时自动忽略（不报错）
3. **向前兼容：** 旧版系统导入新版导出时
   - 忽略不识别的字段
   - 给出明确的警告信息（"以下 N 个字段在当前版本中不被支持：xxx"）
   - 核心数据（角色、世界书、预设）无损导入
4. **迁移工具：** 提供 `migrate-backup` CLI 命令
   - `nesttalk backup migrate v1-v2.json --from v1 --to v3`
   - 自动转换字段结构
5. **校验机制：** SHA256 校验和防止文件损坏
6. **数据脱敏：** 导出时自动移除 API Key 等敏感信息（替换为 `***REDACTED***`），导入时提示用户重新填写

**导入流程：**
```
用户上传备份文件
  → 校验 checksum
  → 检查版本号
  → 如果版本低于当前 → 自动迁移
  → 如果版本高于当前 → 警告 + 尽力导入
  → 预览将要导入的数据
  → 用户确认
  → 执行导入
  → 报告结果
```

### 3.11 Token 优化策略

- 上下文窗口管理：超出 token 限制时自动压缩
- 世界书按需注入：只激活匹配的条目
- 对话摘要：超过 N 轮的对话自动摘要代替完整历史
- Prompt 精简：模板智能裁剪空白/冗余
- 记忆检索限制：每次只注入 Top-K 最相关记忆
- 增量对话：只发送新消息 + 必要上下文，不全量重发

### 3.12 插件系统

- 插件热加载
- 标准插件接口（on_message, on_startup, on_shutdown, register_command）
- 官方插件：天气查询、新闻推送、翻译、游戏互动
- 社区插件市场（远期）

---

## 四、数据流

```
用户发消息
  │
  ▼
平台适配器接收
  │
  ▼
消息预处理器
  ├── 图片 → Vision API → 文字描述
  ├── 语音 → STT → 文字
  └── 文本 → 直接传递
  │
  ▼
记忆检索（RAG）
  ├── 用户画像
  ├── 相关长期记忆（Top-K）
  └── 近期对话摘要
  │
  ▼
世界书引擎
  ├── 扫描对话历史 → 关键词匹配
  ├── 递归触发条目
  └── Token预算控制 → 选中的条目
  │
  ▼
预设引擎
  ├── 拼装 System Prompt
  ├── 注入角色信息
  ├── 注入世界书条目
  ├── 注入记忆
  └── 注入对话历史
  │
  ▼
LLM 调用（Tool Use 模式）
  ├── 正常回复 → 直接输出
  ├── 需要生图 → 调用 ImageGen Tool
  ├── 需要语音 → 调用 TTS Tool
  └── 需要识图 → 调用 Vision Tool
  │
  ▼
后处理器
  ├── 敏感内容过滤
  ├── 格式化
  └── 多模态附件生成
  │
  ▼
平台适配器发送
  │
  ▼
用户收到回复
```

---

## 五、项目结构

```
nesttalk/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/
│   │   │   ├── character/    # 角色服务
│   │   │   ├── worldbook/    # 世界书引擎
│   │   │   ├── preset/       # 预设引擎
│   │   │   ├── llm_gateway/  # LLM 网关
│   │   │   ├── multimodal/   # 多模态引擎
│   │   │   ├── memory/       # 记忆系统
│   │   │   ├── proactive/    # 主动交互
│   │   │   ├── platform/     # 平台适配器
│   │   │   ├── chat/         # 对话核心
│   │   │   └── backup/       # 备份迁移
│   │   └── plugins/          # 插件系统
│   ├── migrations/           # 数据库迁移
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/            # 页面
│   │   ├── components/       # 组件
│   │   ├── stores/           # 状态管理
│   │   ├── api/              # API 封装
│   │   └── utils/            # 工具函数
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 六、开发阶段规划

### 第一阶段：MVP（最小可行产品）
- ✅ 角色卡导入（V2/V3/CHARX）
- ✅ LLM 网关（OpenAI + DeepSeek）
- ✅ Telegram 平台适配器
- ✅ 基础对话（含角色扮演）
- ✅ 基础后台面板（角色管理 + 对话监控）
- ✅ 一键数据备份导出

### 第二阶段：世界书 & 预设 & 多平台
- ✅ 世界书完整引擎
- ✅ 预设模板系统
- ✅ QQ 适配器
- ✅ 微信适配器
- ✅ 面板功能完善

### 第三阶段：记忆 & 多模态 & 主动交互
- ✅ 长期记忆 RAG 系统
- ✅ 多模态引擎（Vision/Image/STT/TTS）
- ✅ 主动交互引擎
- ✅ 用户自定义多模态模型配置

### 第四阶段：打磨 & 扩展
- ✅ 插件系统
- ✅ 高级分析面板
- ✅ 性能优化
- ✅ PWA 移动端
- ✅ 版本兼容迁移工具

---

## 七、关键设计决策记录

| 决策 | 选择 | 原因 |
|------|------|------|
| 后端语言 | Python | AI生态最丰富，LLM/向量库支持最好 |
| 前端框架 | Vue 3 | 学习曲线低，移动端组件成熟 |
| UI 库 | Naive UI | 移动端适配好，组件美观 |
| 向量数据库 | ChromaDB | 轻量级，嵌入式部署，够用 |
| 消息队列 | Redis | 已有缓存，复用做队列 |
| 备份策略 | 版本化 JSON | 可读、可手动修复、兼容性好 |

---

*皮皮 / 2026-05-15*
