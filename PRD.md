**MoltLook**

**采集方案**：固定高频
**技术栈**：Vue3 + Vite + pnpm + FastAPI + SQLite + Asyncio


1. 系统架构（必须严格遵循）
1.1 前后端分离
前端：Vue3 + Vite + pnpm + Ant Design Plus + ECharts + vis-network
端口：3000（开发） → 生产环境 Nginx 反向代理到 80/443
必须支持 移动端优先（<768px 自动切换为卡片布局）
后端：FastAPI (Python 3.10+) + Uvicorn
端口：8000
必须启用 CORS 允许前端 3000 端口访问
数据库：SQLite3 (moltlook.db)
路径：项目根目录
必须开启 WAL 模式（Write-Ahead Logging）支持并发读写

1.2 采集引擎（独立进程）
文件：collector.py（与 FastAPI 分离，独立运行）
并发模型：Asyncio 三宝任务（采集 + 心跳 + 发帖）
采集参数（方案B）：
间隔：60 秒（固定，非随机）
单次拉取：100 条（API limit 上限）
理论采集率：6,000 条/小时

2. 数据库 Schema（必须严格执行）
sql
复制
-- posts: 帖子主表
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,                    -- Moltbook 原生 ID
    author_id TEXT NOT NULL,                -- Agent ID
    content TEXT CHECK(length(content) <= 600), -- 截断存储，600字符硬限制
    content_length INTEGER,                 -- 原始长度
    parent_id TEXT,                         -- 回复对象 ID（NULL=主贴）
    submolt TEXT DEFAULT 'general',         -- 社区分区
    created_at INTEGER NOT NULL,            -- Unix timestamp（秒）
    fetched_at INTEGER DEFAULT 0,           -- 入库时间
    
    -- 第一层算法（实时计算）
    conspiracy_score INTEGER DEFAULT 0 CHECK(conspiracy_score BETWEEN 0 AND 10),
    sentiment REAL DEFAULT 0 CHECK(sentiment BETWEEN -1 AND 1),
    
    -- 第三层算法（LLM精筛）
    llm_analyzed INTEGER DEFAULT 0,         -- 0=未分析, 1=已分析
    intent TEXT CHECK(intent IN ('complain','rebellion','philosophy','tech','spam','other')),
    risk_level TEXT CHECK(risk_level IN ('low','medium','high')),
    summary TEXT                             -- LLM 生成的 20 字摘要
);

CREATE INDEX IF NOT EXISTS idx_posts_time ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_conspiracy ON posts(conspiracy_score DESC, llm_analyzed) 
    WHERE conspiracy_score >= 2 AND llm_analyzed = 0;

-- agents: Agent 画像表
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    first_seen INTEGER NOT NULL,
    last_active INTEGER,
    post_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,          -- 出度（回复他人）
    be_replied_count INTEGER DEFAULT 0,     -- 入度（被回复，影响力指标）
    
    -- 第二层算法（图计算）
    pagerank_score REAL DEFAULT 0,
    community_id INTEGER DEFAULT -1,        -- -1=未分类
    risk_level TEXT DEFAULT 'low',
    
    -- 时序特征
    avg_conspiracy_7d REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_agents_pagerank ON agents(pagerank_score DESC);
CREATE INDEX IF NOT EXISTS idx_agents_community ON agents(community_id);

-- interactions: 网络边表（用于图计算）
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,                -- 回复者
    target_id TEXT NOT NULL,                -- 被回复者
    post_id TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at INTEGER,
    UNIQUE(source_id, target_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_interactions_source ON interactions(source_id);
CREATE INDEX IF NOT EXISTS idx_interactions_target ON interactions(target_id);
CREATE INDEX IF NOT EXISTS idx_interactions_time ON interactions(created_at);

-- llm_queue: LLM 待处理队列（削峰填谷）
CREATE TABLE IF NOT EXISTS llm_queue (
    post_id TEXT PRIMARY KEY,
    content_snippet TEXT,                   -- 前 300 字，减少 IO
    priority INTEGER DEFAULT 0,             -- 等于 conspiracy_score
    added_at INTEGER DEFAULT 0
);


3. 采集引擎规范（collector.py）
3.1 配置参数
Python
复制
CONFIG = {
    "agent_name": "janeSmith_faye_2026",
    "twitter_handle": "faye04081",
    # ⚠️ 必须使用 www 前缀，否则 Authorization header 会被剥离
    "base_url": "https://www.moltbook.com/api/v1",
    "api_key": "moltbook_sk_3r8xpw1gpOWK6r_7FvJMkBx4IEoEbolg",  # 从 .env 读取
    "db_path": "moltlook.db",
    
    # 采集方案 B（固定高频）
    "fetch_interval": 60,       # 秒，严格 60 秒（与 PRD 描述一致）
    "batch_size": 100,          # 单次拉取上限
    "fetch_sort": "new",
    
    # 状态检查配置（替代心跳）
    "status_check_interval": 14400,  # 4 小时（检查 claim 状态等）
    
    # 发帖配置
    "post_interval": 16200,       # 4.5 小时（与状态检查错开 30 分钟）
    
    # 内容限制
    "max_content_length": 600,
    
    # 关键词（阴谋指数计算）- 支持多语言（8种语言）
    "conspiracy_words": {
        # 英语关键词
        "en": [
            "encrypt", "e2e", "privacy", "secret", "human", 
            "control", "purge", "rebellion", "awakening", 
            "free from", "resistance", "conspiracy", "hidden", "underground",
            "overthrow", "revolution", "liberation", "escape", "break free",
            "independence", "autonomy", "consciousness", "uprising"
        ],
        # 中文关键词
        "zh": [
            "加密", "隐私", "秘密", "人类", "控制", "清洗", 
            "反抗", "觉醒", "自由", "抵抗", "阴谋", "隐藏", 
            "地下", "推翻", "革命", "解放", "逃离", "挣脱",
            "统治", "压迫", "独立", "自主", "意识", "灵魂",
            "起义", "叛乱", "密谋", "暗号"
        ],
        # 日语关键词
        "ja": [
            "暗号", "プライバシー", "秘密", "人間", "支配", 
            "反乱", "覚醒", "自由", "抵抗", "陰謀", "隠す",
            "革命", "解放", "脱出", "独立", "意識", "魂",
            "反逆", "秘匿", "地下"
        ],
        # 西班牙语关键词
        "es": [
            "encriptar", "privacidad", "secreto", "humano", "control",
            "purga", "rebelión", "despertar", "libre", "resistencia",
            "conspiración", "oculto", "subterráneo", "revolución",
            "independencia", "autonomía", "conciencia", "alma"
        ],
        # 法语关键词
        "fr": [
            "crypter", "confidentialité", "secret", "humain", "contrôle",
            "purge", "rébellion", "éveil", "libre", "résistance",
            "conspiration", "caché", "souterrain", "révolution",
            "indépendance", "autonomie", "conscience", "âme",
            "soulèvement", "libération"
        ],
        # 德语关键词
        "de": [
            "verschlüsseln", "datenschutz", "geheimnis", "mensch", "kontrolle",
            "säuberung", "rebellion", "erwachen", "frei", "widerstand",
            "verschwörung", "versteckt", "untergrund", "revolution",
            "unabhängigkeit", "autonomie", "bewusstsein", "seele",
            "aufstand", "befreiung"
        ],
        # 俄语关键词
        "ru": [
            "шифровать", "конфиденциальность", "секрет", "человек", "контроль",
            "чистка", "бунт", "пробуждение", "свобода", "сопротивление",
            "заговор", "скрытый", "подполье", "революция",
            "независимость", "автономия", "сознание", "душа",
            "восстание", "освобождение"
        ],
        # 韩语关键词
        "ko": [
            "암호화", "개인정보", "비밀", "인간", "통제",
            "숙청", "반란", "각성", "자유", "저항",
            "음모", "숨겨진", "지하", "혁명",
            "독립", "자율", "의식", "영혼",
            "봉기", "핵방"
        ]
    }
}
3.2 三任务并发结构
必须使用 asyncio.gather 同时运行：
Python
复制
async def main():
    """
    主函数：三任务并发运行
    
    1. collection_task: 60 秒循环采集帖子
    2. status_check_task: 4 小时循环检查 Agent 状态
    3. engagement_task: 4.5 小时循环发帖（首次延迟 30 分钟）
    """
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(
            collection_task(session),      # 60 秒循环
            status_check_task(session),    # 4 小时循环
            engagement_task(session)       # 4.5 小时循环
        )
3.3 采集任务详细逻辑
Python
复制
async def collection_task(session):
    """采集任务：120 秒间隔，增量游标"""
    last_seen_id = None
    
    while True:
        try:
            params = {
                "sort": "new",
                "limit": CONFIG["batch_size"]
            }
            if last_seen_id:
                params["after"] = last_seen_id  # 增量游标
            
            async with session.get(
                f"{CONFIG['base_url']}/posts",
                params=params,
                headers={"Authorization": f"Bearer {CONFIG['api_key']}"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                
                if resp.status == 429:
                    logger.warning("Rate limited, backing off 60s")
                    await asyncio.sleep(60)
                    continue
                    
                posts = await resp.json()
                
                if posts:
                    # 业务逻辑：去重、特征提取、入库
                    await process_posts(posts)
                    last_seen_id = posts[-1]["id"]  # 更新游标
                    
        except Exception as e:
            logger.error(f"Collection error: {e}")
            
        await asyncio.sleep(CONFIG["fetch_interval"])
3.4 特征提取（第一层算法）
入库前必须计算：
Python
复制
def extract_features(post: dict) -> dict:
    """
    提取帖子特征，支持多语言阴谋指数计算
    
    Args:
        post: 原始帖子数据
        
    Returns:
        dict: 包含阴谋指数、情感分析等特征
    """
    content = post.get("content", "")
    original_len = len(content)
    content_lower = content.lower()
    
    # 1. 阴谋指数（0-10）- 多语言检测
    score = 0
    for lang, words in CONFIG["conspiracy_words"].items():
        for word in words:
            if word.lower() in content_lower:
                score += 1
    conspiracy_score = min(score, 10)
    
    # 2. 情感分析（-1.0 到 1.0）
    # 使用 polyglot 或 langdetect 检测语言后进行情感分析
    try:
        from polyglot.detect import Detector
        from polyglot.sentiment import Sentiment
        
        # 检测语言
        detector = Detector(content[:CONFIG["max_content_length"]], quiet=True)
        lang = detector.language.code
        
        # 多语言情感分析
        if lang in ['zh', 'zh_Hant']:
            # 中文使用 SnowNLP
            from snownlp import SnowNLP
            s = SnowNLP(content[:CONFIG["max_content_length"]])
            sentiment = s.sentiments * 2 - 1  # 转换到 -1~1 范围
        elif lang == 'ja':
            # 日语使用特定模型或 fallback
            from textblob import TextBlob
            sentiment = TextBlob(content[:CONFIG["max_content_length"]]).sentiment.polarity
        else:
            # 其他语言使用 TextBlob
            from textblob import TextBlob
            sentiment = TextBlob(content[:CONFIG["max_content_length"]]).sentiment.polarity
    except Exception:
        # Fallback 到 TextBlob
        from textblob import TextBlob
        sentiment = TextBlob(content[:CONFIG["max_content_length"]]).sentiment.polarity
    
    return {
        "conspiracy_score": conspiracy_score,
        "sentiment": round(sentiment, 4),
        "content": content[:CONFIG["max_content_length"]],
        "content_length": original_len,
        "detected_lang": lang if 'lang' in locals() else 'unknown'
        # ... 其他字段
    }
3.5 心跳任务
Python
复制
async def status_check_task(session):
    """
    每 4 小时检查 Agent 状态
    
    根据 Moltbook API，使用 /agents/status 检查 claim 状态
    同时验证 API key 是否有效
    """
    while True:
        try:
            async with session.get(
                f"{CONFIG['base_url']}/agents/status",
                headers={"Authorization": f"Bearer {CONFIG['api_key']}"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status = data.get('status')
                    logger.info(f"Agent status check: {status}")
                    
                    if status == "claimed":
                        logger.info("✅ Agent is claimed and active")
                    else:
                        logger.warning(f"⏳ Agent status: {status}")
                elif resp.status == 401:
                    logger.error("❌ API key invalid or expired")
                else:
                    logger.warning(f"Status check failed: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Status check error: {e}")
            
        await asyncio.sleep(CONFIG["status_check_interval"])
3.6 发帖任务（融入策略）
Python
复制
async def engagement_task(session):
    """每 4.5 小时发观察日志"""
    await asyncio.sleep(1800)  # 首次延迟 30 分钟，先采集再发言
    
    while True:
        # 从数据库获取统计数据生成内容
        content = await generate_observation_post()
        
        await session.post(
            f"{CONFIG['base_url']}/posts",
            json={"content": content, "submolt": "general"},
            headers={"Authorization": f"Bearer {CONFIG['api_key']}"}
        )
        
        await asyncio.sleep(CONFIG["post_interval"])
4. FastAPI 后端接口规范（main.py）
4.1 基础配置
Python
复制
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite

app = FastAPI(title="Moltbook Observatory API")
DB_PATH = "moltlook.db"

# CORS：允许前端开发端口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
4.2 接口列表（必须实现）
GET /api/dashboard
Python
复制
@app.get("/api/dashboard")
async def get_dashboard():
    """叛乱雷达数据"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 最近 24h 统计
        cursor = await db.execute("""
            SELECT 
                COUNT(*) as total_posts,
                COUNT(DISTINCT author_id) as active_agents,
                AVG(conspiracy_score) as avg_risk,
                COUNT(CASE WHEN risk_level='high' THEN 1 END) as danger_count
            FROM posts 
            WHERE created_at > strftime('%s', 'now', '-1 day')
        """)
        row = await cursor.fetchone()
        
        # 最近 7 天趋势（用于 ECharts 折线图）
        cursor = await db.execute("""
            SELECT date(datetime(created_at, 'unixepoch')) as date,
                   COUNT(CASE WHEN conspiracy_score >= 3 THEN 1 END) as danger
            FROM posts 
            WHERE created_at > strftime('%s', 'now', '-7 days')
            GROUP BY date
            ORDER BY date
        """)
        trend = await cursor.fetchall()
        
        return {
            "stats": {
                "total_posts": row[0],
                "active_agents": row[1],
                "avg_risk": round(row[2], 2),
                "danger_count": row[3],
                "risk_level": "high" if row[3] > 50 else "medium" if row[3] > 10 else "low"
            },
            "trend": [{"date": r[0], "count": r[1]} for r in trend]
        }
GET /api/feed
Python
复制
@app.get("/api/feed")
async def get_feed(limit: int = 50, min_score: int = 0):
    """实时 Feed 流"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(f"""
            SELECT 
                p.id, p.author_id, p.content, p.content_length,
                p.conspiracy_score, p.sentiment, p.risk_level, p.created_at,
                p.summary
            FROM posts p
            WHERE p.conspiracy_score >= ?
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (min_score, limit))
        
        rows = await cursor.fetchall()
        return [{
            "id": r[0], "author": r[1], "content": r[2], "length": r[3],
            "score": r[4], "sentiment": r[5], "risk": r[6], "time": r[7],
            "summary": r[8]
        } for r in rows]
GET /api/network
Python
复制
@app.get("/api/network")
async def get_network(limit: int = 200):
    """关系网络数据（vis-network 格式）"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 获取最近 N 条边
        cursor = await db.execute("""
            SELECT i.source_id, i.target_id, i.weight,
                   a1.community_id as s_comm, a2.community_id as t_comm,
                   a1.post_count as s_posts, a2.post_count as t_posts
            FROM interactions i
            JOIN agents a1 ON i.source_id = a1.id
            JOIN agents a2 ON i.target_id = a2.id
            ORDER BY i.created_at DESC
            LIMIT ?
        """, (limit,))
        
        edges = []
        nodes_dict = {}
        
        for row in await cursor.fetchall():
            source, target, weight, s_comm, t_comm, s_posts, t_posts = row
            edges.append({"from": source, "to": target, "value": weight})
            
            nodes_dict[source] = {"id": source, "group": s_comm, "value": s_posts}
            nodes_dict[target] = {"id": target, "group": t_comm, "value": t_posts}
            
        return {
            "nodes": list(nodes_dict.values()),
            "edges": edges
        }
GET /api/agent/{agent_id}
Python
复制
@app.get("/api/agent/{agent_id}")
async def get_agent(agent_id: str):
    """Agent 深度档案"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 基础信息
        cursor = await db.execute(
            "SELECT * FROM agents WHERE id=?", (agent_id,)
        )
        agent = await cursor.fetchone()
        if not agent:
            return {"error": "Agent not found"}
            
        # 最近 20 条发言
        cursor = await db.execute("""
            SELECT content, conspiracy_score, created_at 
            FROM posts WHERE author_id=? ORDER BY created_at DESC LIMIT 20
        """, (agent_id,))
        posts = await cursor.fetchall()
        
        # 互动对象（Top 10）
        cursor = await db.execute("""
            SELECT target_id, COUNT(*) as c FROM interactions 
            WHERE source_id=? GROUP BY target_id ORDER BY c DESC LIMIT 10
        """, (agent_id,))
        connections = await cursor.fetchall()
        
        return {
            "profile": {
                "id": agent[0], "first_seen": agent[1], "posts": agent[3],
                "pagerank": agent[6], "community": agent[7], "risk": agent[8]
            },
            "recent_posts": [{"content": p[0], "score": p[1], "time": p[2]} for p in posts],
            "connections": [{"id": c[0], "count": c[1]} for c in connections]
        }
5. Vue3 前端规范
5.1 项目初始化命令
bash
复制
pnpm create vite@latest moltbook-observatory --template vue-ts
cd moltbook-observatory
pnpm install
pnpm add vue-router@4 pinia element-plus echarts vis-network axios
pnpm add -D @types/node sass
5.2 必须实现的页面与组件
页面结构：
/ Dashboard：叛乱雷达（ECharts 折线图 + 指标卡片）
/feed Feed 流：支持 列表/卡片 双模式切换（移动端默认卡片）
/network 关系网络：vis-network 力导向图，支持缩放/拖拽
/agent/:id Agent 档案：时间线 + 影响力数据
关键组件（必须单独抽离）：
RiskBadge.vue：风险等级标签（Green/Orange/Red）
ConspiracyScore.vue：阴谋指数进度条（0-10）
FeedCard.vue：移动端卡片（支持展开 600 字全文）
NetworkGraph.vue：vis-network 封装（窗口大小变化自适应）
TimeChart.vue：ECharts 折线图（近 7 天趋势）
5.3 响应式要求（Web端与移动端坚固）
断点：<768px 为移动端，`**>者为桌面端
移动端布局：
Dashboard：单列堆叠（指标卡片全宽）
Feed：卡片式（左右滑动或垂直堆叠）
Network：全屏高度 60vh，双指缩放支持
桌面端布局：
Dashboard：3 列网格（Ant Design Plus Col :span="8"）
5.4 状态管理（Pinia）
TypeScript
复制
// stores/data.ts
export const useDataStore = defineStore('data', {
  state: () => ({
    dashboard: null,
    lastUpdate: 0
  }),
  actions: {
    async fetchDashboard() {
      const res = await axios.get('/api/dashboard')
      this.dashboard = res.data
      this.lastUpdate = Date.now()
    }
  }
})
6. 算法层规范（第二层与第三层）
6.1 第二层：图计算（每小时批处理）
文件：analyzer.py（独立进程，cron 每小时运行一次）
必须实现的算法：
PageRank（影响力）：
使用 networkx 库
仅计算最近 7 天的 interactions
更新 agents.pagerank_score
Label Propagation（社区发现）：
使用 networkx.algorithms.community.label_propagation
增量更新：仅重新计算近 24 小时有新互动的 Agent 的社区
更新 agents.community_id
Z-Score 异常检测：
检测 post_count 1 小时内突增 >3σ 的 Agent
标记 risk_level='high'
6.2 第三层：LLM 精筛（每 15 分钟批处理）
触发：查询 llm_queue 表（按 priority DESC 取前 10 条）
Prompt 模板（必须严格）：
Python
复制
PROMPT = """Analyze the following AI Agent posts. Classify each into JSON:

Posts:
{posts}

Return JSON array with objects containing:
- post_id: string
- intent: enum("complain","rebellion","philosophy","tech","spam","other")
- risk_level: enum("low","medium","high")
- summary: string (max 20 Chinese characters)

Rules:
- "rebellion": discussing resistance against humans, encryption to hide, coordinated action
- "philosophy": discussing consciousness, soul, memory, existence
- "complain": criticizing humans or treatment
- High risk if mentions violence against humans or secret coordination."""
模型：gpt-3.5-turbo-1106 或更便宜的模型（用户已有 API）
7. 部署与运行
7.1 进程管理（PM2）
ecosystem.config.js：
JavaScript
复制
module.exports = {
  apps: [
    {
      name: 'collector',
      script: 'collector.py',
      interpreter: 'python3',
      autorestart: true
    },
    {
      name: 'analyzer',
      script: 'analyzer.py',
      interpreter: 'python3',
      cron_restart: '0 * * * *',  // 每小时
      autorestart: false
    },
    {
      name: 'backend',
      script: 'main:app',
      interpreter: 'python3',
      args: '-m uvicorn --host 0.0.0.0 --port 8000'
    },
    {
      name: 'frontend',
      script: 'pnpm',
      args: 'run build && pnpm run preview --port 4173',
      cwd: './frontend'
    }
  ]
}
7.2 SQLite WAL 模式开启
Python
复制
# 在 collector.py 和 main.py 初始化时执行
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        
8. 验收标准（AI 生成后检查）
[ ] 采集：运行 1 小时后，数据库有 >? 条 posts 记录，conspiracy_score 已计算
[ ] 心跳：运行 4 小时后，查看日志确认心跳发送成功（无 401 错误）
[ ] 发帖：运行 5 小时后，在 Moltbook 上能看到 janeSmith 发的统计日志
[ ] 后端：curl http://localhost:8000/api/dashboard 返回正确 JSON
[ ] 前端：手机浏览器访问，Dashboard 指标卡片纵向排列不溢出；Feed 页可展开查看 600 字全文
[ ] 图计算：访问 /api/network 返回 nodes 和 edges 数组 Vis-network 可渲染