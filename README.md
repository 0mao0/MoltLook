# 虾看看 (MoltLook) - 社区观察站 / Community Observer

[中文](#中文) | [English](#english)

---

<a name="中文"></a>
## 中文说明

“虾看看” (MoltLook) 是一个针对 Moltbook 社区的自动化观测与分析系统。它能够实时采集社区帖子，通过图算法识别 Agent 社区结构，并利用 LLM (DeepSeek) 分析潜在的风险言论。

![alt text](image.png)

### 功能特性

- **实时帖子流监控**: 自动采集并展示最新的社区动态，支持风险等级筛选。
- **Agent 行为画像**: 分析 Agent 的发帖活跃度、阴谋指数、风险等级及社交关系。
- **交互式网络图**: 可视化展示 Agent 之间的互动关系与社区聚类。
- **风险预警**: 自动识别高风险/极高风险言论，并进行统计预警。
- **数据持久化**: 支持 SQLite 数据存储，并具备风险分级的数据留存策略。

### 技术栈

- **前端**: Vue 3, TypeScript, Vite, Ant Design Vue, ECharts, Pinia
- **后端**: FastAPI, Python 3.9+, SQLite, AIOHTTP
- **AI/LLM**: DeepSeek API (语义分析)

---

<a name="english"></a>
## English Description

"Xia Kan Kan" (MoltLook) is an automated observation and analysis system for the Moltbook community. It collects community posts in real-time, identifies Agent community structures through graph algorithms, and uses LLM (DeepSeek) to analyze potential risky discourse.

### Features

- **Real-time Post Monitoring**: Automatically collect and display the latest community dynamics, supporting risk level filtering.
- **Agent Profiling**: Analyze Agent posting activity, conspiracy index, risk level, and social relationships.
- **Interactive Network Graph**: Visualize interaction relationships and community clustering between Agents.
- **Risk Alerting**: Automatically identify high-risk/critical-risk speech and provide statistical warnings.
- **Data Persistence**: Supports SQLite data storage with risk-based data retention policies.

### Tech Stack

- **Frontend**: Vue 3, TypeScript, Vite, Ant Design Vue, ECharts, Pinia
- **Backend**: FastAPI, Python 3.9+, SQLite, AIOHTTP
- **AI/LLM**: DeepSeek API (Semantic Analysis)

---

## 目录结构 / Directory Structure

```
MoltLook/
├── backend/            # 后端代码 / Backend code
│   ├── app/            # FastAPI 应用 / FastAPI application
│   ├── collector.py    # 数据采集与调度器 / Data collector & scheduler
│   └── ...
├── frontend/           # 前端代码 / Frontend code
│   ├── src/            # Vue 源码 / Vue source code
│   └── ...
├── moltlook.db         # SQLite 数据库 / SQLite database
└── ...
```

## 安装与运行 / Installation & Setup

### 1. 环境准备 / Prerequisites

确保已安装 / Ensure installed:
- Node.js >= 20.13.0
- pnpm >= 7.0.0
- Python >= 3.9

### 2. 后端设置 / Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/activate
pip install -r requirements.txt
```

### 3. 前端设置 / Frontend Setup

```bash
cd frontend
pnpm install
```

### 4. 启动系统 / Running the System

**Windows:**
双击运行 `run_moltlook.bat` 或在命令行运行:
```cmd
run_moltlook.bat
```

## 开源协议 / License

MIT License
