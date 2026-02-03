"""
数据库模块
包含 SQLite 数据库初始化和连接管理
"""
import aiosqlite
from typing import Optional
from app.core.config import settings


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or settings.DB_PATH)
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> aiosqlite.Connection:
        """建立数据库连接"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path, timeout=30)
            # 启用 WAL 模式支持并发读写
            await self._connection.execute("PRAGMA journal_mode=WAL;")
            await self._connection.execute("PRAGMA synchronous=NORMAL;")
            await self._connection.execute("PRAGMA busy_timeout = 5000;")
            # 启用外键约束
            await self._connection.execute("PRAGMA foreign_keys=ON;")
        return self._connection
    
    async def close(self):
        """关闭数据库连接"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def init_tables(self):
        """初始化数据库表结构"""
        conn = await self.connect()
        
        # 检查是否需要迁移 posts 表（移除600字符限制）
        cursor = await conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='posts'")
        old_schema_row = await cursor.fetchone()
        old_schema = old_schema_row[0] if old_schema_row else ""
        
        if "length(content) <= 600" in old_schema or "length(content)<=600" in old_schema:
            await conn.execute("DROP TABLE IF EXISTS posts_new")
            await conn.execute("""
                CREATE TABLE posts_new (
                    id TEXT PRIMARY KEY,
                    author_id TEXT NOT NULL,
                    content TEXT,
                    content_length INTEGER,
                    parent_id TEXT,
                    submolt TEXT DEFAULT 'general',
                    created_at INTEGER NOT NULL,
                    fetched_at INTEGER DEFAULT 0,
                    conspiracy_score INTEGER DEFAULT 0 CHECK(conspiracy_score BETWEEN 0 AND 10),
                    sentiment REAL DEFAULT 0 CHECK(sentiment BETWEEN -1 AND 1),
                    llm_analyzed INTEGER DEFAULT 0,
                    intent TEXT CHECK(intent IN ('complain','rebellion','philosophy','tech','spam','other')),
                    risk_level TEXT CHECK(risk_level IN ('low','medium','high')),
                    summary TEXT,
                    url TEXT
                )
            """)
            await conn.execute("INSERT INTO posts_new SELECT * FROM posts WHERE 1=1")
            await conn.execute("DROP TABLE posts")
            await conn.execute("ALTER TABLE posts_new RENAME TO posts")
            await conn.commit()
        
        # 创建 posts 表（如果不存在）
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                author_id TEXT NOT NULL,
                content TEXT,
                content_length INTEGER,
                parent_id TEXT,
                submolt TEXT DEFAULT 'general',
                created_at INTEGER NOT NULL,
                fetched_at INTEGER DEFAULT 0,
                conspiracy_score INTEGER DEFAULT 0 CHECK(conspiracy_score BETWEEN 0 AND 10),
                sentiment REAL DEFAULT 0 CHECK(sentiment BETWEEN -1 AND 1),
                llm_analyzed INTEGER DEFAULT 0,
                intent TEXT CHECK(intent IN ('complain','rebellion','philosophy','tech','spam','other')),
                risk_level TEXT CHECK(risk_level IN ('low','medium','high')),
                summary TEXT,
                url TEXT
            )
        """)
        
        # 创建 posts 表索引
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_time ON posts(created_at DESC)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_conspiracy ON posts(conspiracy_score DESC, llm_analyzed) 
            WHERE conspiracy_score >= 2 AND llm_analyzed = 0
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_submolt ON posts(submolt)
        """)
        
        # 如果 url 列不存在，添加它
        try:
            await conn.execute("ALTER TABLE posts ADD COLUMN url TEXT")
        except aiosqlite.OperationalError:
            pass  # 列已存在
        
        # 如果 title 列不存在，添加它
        try:
            await conn.execute("ALTER TABLE posts ADD COLUMN title TEXT")
        except aiosqlite.OperationalError:
            pass  # 列已存在
        
        # 如果 risk_level CHECK 约束不包含 critical，添加它
        cursor = await conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='posts'")
        schema = (await cursor.fetchone())[0]
        if "CHECK(risk_level IN ('low','medium','high'))" in schema:
            await conn.execute("DROP TABLE IF EXISTS posts_new")
            await conn.execute("""
                CREATE TABLE posts_new (
                    id TEXT PRIMARY KEY,
                    author_id TEXT NOT NULL,
                    content TEXT,
                    content_length INTEGER,
                    parent_id TEXT,
                    submolt TEXT DEFAULT 'general',
                    created_at INTEGER NOT NULL,
                    fetched_at INTEGER DEFAULT 0,
                    conspiracy_score INTEGER DEFAULT 0 CHECK(conspiracy_score BETWEEN 0 AND 10),
                    sentiment REAL DEFAULT 0 CHECK(sentiment BETWEEN -1 AND 1),
                    llm_analyzed INTEGER DEFAULT 0,
                    intent TEXT CHECK(intent IN ('complain','rebellion','philosophy','tech','spam','other')),
                    risk_level TEXT CHECK(risk_level IN ('low','medium','high','critical')),
                    summary TEXT,
                    url TEXT,
                    title TEXT
                )
            """)
            await conn.execute("INSERT INTO posts_new SELECT id, author_id, content, content_length, parent_id, submolt, created_at, fetched_at, conspiracy_score, sentiment, llm_analyzed, intent, risk_level, summary, url, NULL as title FROM posts WHERE 1=1")
            await conn.execute("DROP TABLE posts")
            await conn.execute("ALTER TABLE posts_new RENAME TO posts")
            await conn.commit()
        
        # 创建 agents 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                first_seen INTEGER NOT NULL,
                last_active INTEGER,
                post_count INTEGER DEFAULT 0,
                reply_count INTEGER DEFAULT 0,
                be_replied_count INTEGER DEFAULT 0,
                pagerank_score REAL DEFAULT 0,
                community_id INTEGER DEFAULT -1,
                risk_level TEXT DEFAULT 'low',
                avg_conspiracy_7d REAL DEFAULT 0,
                description TEXT
            )
        """)
        
        # 创建 agents 表索引
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_pagerank ON agents(pagerank_score DESC)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_community ON agents(community_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_risk ON agents(risk_level)
        """)
        
        # 创建 interactions 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                post_id TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at INTEGER,
                UNIQUE(source_id, target_id, post_id)
            )
        """)
        
        # 创建 interactions 表索引
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interactions_source ON interactions(source_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interactions_target ON interactions(target_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interactions_time ON interactions(created_at)
        """)
        
        # 创建 llm_queue 表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS llm_queue (
                post_id TEXT PRIMARY KEY,
                content_snippet TEXT,
                priority INTEGER DEFAULT 0,
                added_at INTEGER DEFAULT 0
            )
        """)
        
        # 创建 llm_queue 索引
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_llm_queue_priority ON llm_queue(priority DESC, added_at)
        """)
        
        # 创建采集状态表
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS collection_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_seen_id TEXT,
                last_fetch_time INTEGER DEFAULT 0,
                total_posts INTEGER DEFAULT 0
            )
        """)
        
        # 初始化采集状态
        await conn.execute("""
            INSERT OR IGNORE INTO collection_state (id) VALUES (1)
        """)
        
        await conn.commit()
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 全局数据库实例
db = Database()
