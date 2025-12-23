# Watson 🕵️‍♂️

**Watson** 是一个智能技术导师（AI Technical Coach），旨在通过个性化、迭代式和反思性的对话，帮助用户深入学习编程概念、系统设计和技术原理。

它不仅仅是一个聊天机器人，更是一个由多个智能体（Agents）组成的协作系统，能够自我修正、持续追踪用户的学习进度，并提供量身定制的学习建议。

## 🌟 核心特性

*   **多智能体协作架构 (Multi-Agent Architecture)**:
    *   **🎓 Coach (教练)**: 负责生成回答初稿。它会根据用户的知识画像调整讲解深度，并利用网络搜索获取最新信息。
    *   **🧐 Critic (批评家)**: 负责“代码审查”。它会检查 Coach 的回答是否准确、简洁且切题。如果不满意，它会打回重写（最多 3 轮循环）。
    *   **🧭 Mentor (导师)**: 负责长期规划。它不直接与用户对话，而是默默观察，更新用户的**全局知识画像**（掌握了什么、欠缺什么），并推荐下一步的学习资源。

*   **🔄 自我修正循环 (Self-Correction Loop)**:
    *   Watson 的回答并非一次生成。Coach 和 Critic 会在后台进行多轮辩论和修改，直到达成高质量标准，确保你收到的每一条回答都经过了深思熟虑。

*   **🧠 全局长时记忆 (Long-term Memory)**:
    *   Watson 拥有“记忆”。它会通过 `user_profile` 数据库表记录你的学习目标和知识盲点。无论你开启多少个新对话，它都知道你是谁，你学到了哪里。
    *   **知识画像可视化**: 侧边栏实时展示你的知识技能树（按类别分类）和学习目标，支持一键清空重置。

*   **💬 智能对话管理**:
    *   **自动标题生成**: 根据对话内容自动生成简短标题，方便在侧边栏查找历史记录。
    *   **历史记录管理**: 支持删除单条对话或一键清空所有历史记录。
    *   **流式响应**: 实时流式输出，并支持前端展示内部思考过程（草稿、批评意见、修改记录）。

## 🛠 技术栈

### Backend (后端)
*   **Framework**: FastAPI
*   **Orchestration**: LangGraph (StateGraph, Checkpointing)
*   **LLM Framework**: LangChain
*   **Database**: SQLite (aiosqlite) for state persistence and profile management
*   **Model**: DeepSeek V3 (compatible with OpenAI API format)
*   **Tools**: Custom Web Search (Bocha API)

### Frontend (前端)
*   **Framework**: React (Vite)
*   **Styling**: Tailwind CSS
*   **Components**: Lucide React (Icons), React Markdown, Syntax Highlighter
*   **State Management**: React Hooks

## 🚀 快速开始

### 1. 环境准备
确保你已安装 Python 3.9+ 和 Node.js 18+。

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key:
# DEEPSEEK_API_KEY=sk-...
# DEEPSEEK_BASE_URL=https://api.deepseek.com
# BOCHA_API_KEY=... (用于联网搜索)
```

启动后端服务：
```bash
python main.py
# 服务运行在 http://localhost:8000
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 页面运行在 http://localhost:5173
```

## 📂 项目结构

```
Watson/
├── backend/
│   ├── agent.py          # LangGraph 智能体编排核心逻辑 (Coach/Critic/Mentor)
│   ├── profile.py        # 用户画像管理 (CRUD)
│   ├── tools.py          # 工具定义 (Web Search)
│   ├── prompts.yaml      # Prompt 模板管理
│   ├── routers/          # FastAPI 路由
│   └── main.py           # 程序入口
├── frontend/
│   ├── src/
│   │   ├── pages/Home.tsx  # 主聊天界面
│   │   └── ...
│   └── ...
└── checkpoints.db        # SQLite 数据库 (自动生成)
```

## 🧠 工作流示意

1. **User Input**: 用户提问。
2. **Retrieve Profile**: 系统读取用户的全局知识画像。
3. **Coach Draft**: Coach 生成初稿（可能调用搜索）。
4. **Critic Review**: Critic 评估初稿。
   - -> **Pass**: 进入下一步。
   - -> **Fail**: 返回 Coach 修改（携带修改意见），记录 Revision Count。
5. **Final Generation**: 生成最终回答。
6. **Mentor Analysis**: Mentor 分析本次交互，更新用户画像，生成学习建议。
7. **Response**: 前端渲染最终回答及内部思考过程。

## 📝 License

MIT
