# NestTalk（栖言）

> 🦊 AI 情感陪聊机器人 — 兼容酒馆角色卡/世界书/预设，多平台·多模态·主动交互

## 特性

- 🎭 **兼容酒馆生态** — 支持 Character Card V2/V3 (PNG/CHARX/JSON)、世界书、预设
- 🤖 **多模型支持** — OpenAI / Claude / Gemini / DeepSeek / Ollama 等
- 📱 **多平台触达** — Telegram / QQ / 微信
- 🖼️ **多模态交互** — 识图、生图、语音识别、语音合成，LLM 自动调用
- 🧠 **长期记忆** — RAG 向量检索 + 对话摘要 + 用户画像
- 💓 **主动交互** — 定时问候、情感驱动主动发言，不是问一句答一句
- 📊 **移动端适配后台** — Vue 3 + Naive UI，响应式布局
- 💾 **一键备份** — 版本化导出，向前向后兼容，API Key 自动脱敏
- ⚡ **省 Token** — 智能上下文管理、世界书按需注入、对话自动摘要

## 快速开始

```bash
# 1. 复制配置
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 2. 启动
docker compose up -d

# 3. 访问
# 后台面板: http://localhost:3000
# API 文档: http://localhost:8000/docs
```

## 项目结构

```
nesttalk/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 核心配置 / 数据库
│   │   ├── models/        # SQLAlchemy 模型
│   │   ├── services/      # 业务服务
│   │   │   ├── character/ # 角色导入/管理
│   │   │   ├── worldbook/ # 世界书引擎
│   │   │   ├── preset/    # 预设引擎
│   │   │   ├── llm_gateway/ # LLM 网关
│   │   │   ├── multimodal/ # 多模态引擎
│   │   │   ├── memory/    # 记忆系统
│   │   │   ├── proactive/ # 主动交互
│   │   │   ├── platform/  # 平台适配器
│   │   │   ├── chat/      # 对话核心
│   │   │   └── backup/    # 备份与迁移
│   │   └── plugins/       # 插件系统
│   └── requirements.txt
├── frontend/          # Vue 3 前端
│   └── src/
│       ├── views/         # 页面组件
│       ├── layouts/       # 布局组件
│       ├── stores/        # Pinia 状态管理
│       └── api/           # API 封装
├── docker-compose.yml
└── DESIGN.md          # 完整设计文档
```

## 许可证

MIT
