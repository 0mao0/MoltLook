# MoltLook 社区观察站

MoltLook 是一个针对 Moltbook 社区的自动化观测与分析系统。它能够实时采集社区帖子，通过图算法识别 Agent 社区结构，并利用 LLM (DeepSeek) 分析潜在的阴谋论与风险言论。
![alt text](image.png)

## 功能特性

- **实时帖子流监控**: 自动采集并展示最新的社区动态，支持风险等级筛选。
- **Agent 行为画像**: 分析 Agent 的发帖活跃度、阴谋指数、风险等级及社交关系。
- **交互式网络图**: 可视化展示 Agent 之间的互动关系与社区聚类。
- **风险预警**: 自动识别高风险/极高风险言论，并进行统计预警。
- **数据持久化**: 支持 SQLite 数据存储，并具备风险分级的数据留存策略。

## 技术栈

- **前端**: Vue 3, TypeScript, Vite, Element Plus, ECharts, Pinia
- **后端**: FastAPI, Python 3.9+, SQLite, AIOHTTP
- **AI/LLM**: DeepSeek API (语义分析), Qwen/Other (翻译/辅助)

## 目录结构

```
MoltLook/
├── backend/            # 后端代码
│   ├── app/            # FastAPI 应用
│   ├── collector.py    # 数据采集与调度器 (三宝任务)
│   ├── run_analysis.py # 深度分析脚本
│   └── ...
├── frontend/           # 前端代码
│   ├── src/            # Vue 源码
│   └── ...
├── moltlook.db         # SQLite 数据库
└── ...
```

## 安装与运行

### 1. 环境准备

确保已安装：
- Node.js >= 18.12.0
- pnpm >= 7.0.0
- Python >= 3.9

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 前端设置

```bash
cd frontend

# 安装依赖
pnpm install
```

### 4. 启动系统

推荐使用根目录下的启动脚本：

**Windows:**
双击运行 `run_moltlook.bat`
或者在命令行运行:
```cmd
run_moltlook.bat
```

该脚本会同时启动：
1. 后端 API 服务 (Port 8000)
2. 数据采集器 (Collector - 负责数据抓取、状态检查、发帖互动)
3. 前端开发服务器 (Port 5173)

### 手动启动 (如果不使用脚本)

你需要打开三个终端窗口：

Terminal 1 (API):
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 (Collector - **重要**):
```bash
cd backend
python collector.py
```
*注意：如果不运行 collector.py，系统将不会有新数据进来。*

Terminal 3 (Frontend):
```bash
cd frontend
pnpm run serve
```

## 核心任务说明 (PRD 三宝)

系统严格实现了三大核心定时任务 (见 `backend/collector.py`):
1. **Collection Task (采集)**: 每 60 秒从 Moltbook 获取最新帖子。
2. **Status Check Task (监控)**: 每 4 小时检查 Agent 存活状态。
3. **Engagement Task (干预)**: 每 4.5 小时生成并发布观察报告。

## 开源协议

MIT License
