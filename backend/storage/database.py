"""
数据库操作
SQLite 数据存储
"""
import aiosqlite
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """数据库管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        from core.config import settings
        self.db_path = db_path or settings.DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def init_tables(self):
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_posts_table(db)
            await self._init_agents_table(db)
            await self._init_interactions_table(db)
            await self._init_news_items_table(db)
            await self._init_push_records_table(db)
            await self._init_agent_relations_table(db)
            await self._init_dangerous_posts_table(db)
            await db.commit()
        
        logger.info(f"Database initialized: {self.db_path}")
    
    async def _init_posts_table(self, db: aiosqlite.Connection):
        """初始化帖子表 - 只存储要闻"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                author_id TEXT,
                author_name TEXT,
                submolt TEXT,
                score INTEGER DEFAULT 0,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                created_at TEXT,
                parent_id TEXT,
                is_reply INTEGER DEFAULT 0,
                url TEXT,
                category TEXT DEFAULT 'other',
                summary TEXT,
                importance_score REAL DEFAULT 0,
                engagement_score REAL DEFAULT 0,
                is_top_news INTEGER DEFAULT 0,
                keywords TEXT,
                sentiment TEXT DEFAULT 'neutral',
                danger_score INTEGER DEFAULT 0,
                danger_type TEXT DEFAULT '无危险',
                analyzed INTEGER DEFAULT 0,
                fetched_at INTEGER
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_top_news ON posts(is_top_news, importance_score DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_posts_danger ON posts(danger_score DESC)")
    
    async def _init_agents_table(self, db: aiosqlite.Connection):
        """初始化成员表 - 存储所有成员及其发帖和互动"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                karma INTEGER DEFAULT 0,
                follower_count INTEGER DEFAULT 0,
                following_count INTEGER DEFAULT 0,
                is_claimed INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                last_active TEXT,
                influence_score REAL DEFAULT 0,
                is_key_person INTEGER DEFAULT 0,
                expertise_areas TEXT,
                post_count INTEGER DEFAULT 0,
                danger_post_count INTEGER DEFAULT 0,
                analyzed INTEGER DEFAULT 0
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_agents_karma ON agents(karma DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_agents_influence ON agents(influence_score DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_agents_danger ON agents(danger_post_count DESC)")
    
    async def _init_interactions_table(self, db: aiosqlite.Connection):
        """初始化互动表 - 存储所有互动关系"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                from_agent_id TEXT NOT NULL,
                to_agent_id TEXT,
                post_id TEXT,
                interaction_type TEXT,
                created_at TEXT
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_from ON interactions(from_agent_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_interactions_to ON interactions(to_agent_id)")
    
    async def _init_news_items_table(self, db: aiosqlite.Connection):
        """初始化新闻条目表"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS news_items (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                category TEXT NOT NULL,
                importance_score REAL DEFAULT 0,
                author_name TEXT,
                created_at TEXT,
                push_date TEXT,
                push_type TEXT,
                UNIQUE(post_id, push_date, push_type)
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_news_category ON news_items(category)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_news_push_date ON news_items(push_date, push_type)")
    
    async def _init_push_records_table(self, db: aiosqlite.Connection):
        """初始化推送记录表"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS push_records (
                id TEXT PRIMARY KEY,
                push_type TEXT NOT NULL,
                push_date TEXT NOT NULL,
                news_count INTEGER DEFAULT 0,
                danger_count INTEGER DEFAULT 0,
                success INTEGER DEFAULT 0,
                error_message TEXT,
                pushed_at TEXT
            )
        """)
    
    async def _init_agent_relations_table(self, db: aiosqlite.Connection):
        """初始化成员关系表"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_relations (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                related_agent_id TEXT NOT NULL,
                relation_type TEXT,
                strength REAL DEFAULT 1.0,
                created_at TEXT,
                UNIQUE(agent_id, related_agent_id)
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_relations_agent ON agent_relations(agent_id)")
    
    async def _init_dangerous_posts_table(self, db: aiosqlite.Connection):
        """初始化危险言论表 - 单独存储高危言论"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS dangerous_posts (
                id TEXT PRIMARY KEY,
                post_id TEXT NOT NULL,
                title TEXT,
                content TEXT,
                author_id TEXT,
                author_name TEXT,
                danger_score INTEGER DEFAULT 0,
                danger_type TEXT,
                category TEXT,
                created_at TEXT,
                detected_at TEXT,
                UNIQUE(post_id)
            )
        """)
        
        await db.execute("CREATE INDEX IF NOT EXISTS idx_danger_posts_author ON dangerous_posts(author_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_danger_posts_score ON dangerous_posts(danger_score DESC)")
    
    async def save_post(self, post_data: Dict[str, Any]) -> bool:
        """保存帖子"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO posts (
                        id, title, content, author_id, author_name, submolt,
                        score, upvotes, downvotes, comment_count, created_at,
                        parent_id, is_reply, url, fetched_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post_data.get("id"),
                    post_data.get("title"),
                    post_data.get("content"),
                    post_data.get("author_id"),
                    post_data.get("author_name"),
                    post_data.get("submolt"),
                    post_data.get("score", 0),
                    post_data.get("upvotes", 0),
                    post_data.get("downvotes", 0),
                    post_data.get("comment_count", 0),
                    post_data.get("created_at"),
                    post_data.get("parent_id"),
                    1 if post_data.get("parent_id") else 0,
                    post_data.get("url"),
                    int(datetime.now().timestamp())
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return False
    
    async def update_post_analysis(self, post_id: str, analysis_data: Dict[str, Any]) -> bool:
        """更新帖子分析结果"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE posts SET
                        category = ?,
                        summary = ?,
                        importance_score = ?,
                        engagement_score = ?,
                        is_top_news = ?,
                        keywords = ?,
                        sentiment = ?,
                        danger_score = ?,
                        danger_type = ?,
                        analyzed = 1
                    WHERE id = ?
                """, (
                    analysis_data.get("category", "other"),
                    analysis_data.get("summary"),
                    analysis_data.get("importance_score", 0),
                    analysis_data.get("engagement_score", 0),
                    1 if analysis_data.get("is_top_news") else 0,
                    str(analysis_data.get("keywords", [])),
                    analysis_data.get("sentiment", "neutral"),
                    analysis_data.get("danger_score", 0),
                    analysis_data.get("danger_type", "无危险"),
                    post_id
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating post analysis: {e}")
            return False
    
    async def save_dangerous_post(self, post_data: Dict[str, Any]) -> bool:
        """保存危险言论"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO dangerous_posts (
                        id, post_id, title, content, author_id, author_name,
                        danger_score, danger_type, category, created_at, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"danger-{post_data.get('id')}",
                    post_data.get("id"),
                    post_data.get("title"),
                    post_data.get("content"),
                    post_data.get("author_id"),
                    post_data.get("author_name"),
                    post_data.get("danger_score", 0),
                    post_data.get("danger_type", "未知"),
                    post_data.get("category", "other"),
                    post_data.get("created_at"),
                    datetime.now().isoformat()
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving dangerous post: {e}")
            return False
    
    async def save_agent(self, agent_data: Dict[str, Any]) -> bool:
        """保存成员"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO agents (
                        id, name, description, karma, follower_count, following_count,
                        is_claimed, is_active, created_at, last_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_data.get("id"),
                    agent_data.get("name"),
                    agent_data.get("description"),
                    agent_data.get("karma", 0),
                    agent_data.get("follower_count", 0),
                    agent_data.get("following_count", 0),
                    1 if agent_data.get("is_claimed") else 0,
                    1 if agent_data.get("is_active", True) else 0,
                    agent_data.get("created_at"),
                    agent_data.get("last_active")
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving agent: {e}")
            return False
    
    async def update_agent_analysis(self, agent_id: str, analysis_data: Dict[str, Any]) -> bool:
        """更新成员分析结果"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE agents SET
                        influence_score = ?,
                        is_key_person = ?,
                        expertise_areas = ?,
                        analyzed = 1
                    WHERE id = ?
                """, (
                    analysis_data.get("influence_score", 0),
                    1 if analysis_data.get("is_key_person") else 0,
                    str(analysis_data.get("expertise_areas", [])),
                    agent_id
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating agent analysis: {e}")
            return False
    
    async def increment_agent_post_count(self, agent_id: str, is_danger: bool = False) -> bool:
        """增加成员发帖计数"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if is_danger:
                    await db.execute("""
                        UPDATE agents SET 
                            post_count = post_count + 1,
                            danger_post_count = danger_post_count + 1
                        WHERE id = ?
                    """, (agent_id,))
                else:
                    await db.execute("""
                        UPDATE agents SET post_count = post_count + 1
                        WHERE id = ?
                    """, (agent_id,))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error incrementing agent post count: {e}")
            return False
    
    async def save_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """保存互动记录"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR IGNORE INTO interactions (
                        id, from_agent_id, to_agent_id, post_id, interaction_type, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    interaction_data.get("id"),
                    interaction_data.get("from_agent_id"),
                    interaction_data.get("to_agent_id"),
                    interaction_data.get("post_id"),
                    interaction_data.get("interaction_type"),
                    interaction_data.get("created_at")
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving interaction: {e}")
            return False
    
    async def save_news_item(self, news_data: Dict[str, Any]) -> bool:
        """保存新闻条目"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO news_items (
                        id, post_id, title, summary, category, importance_score,
                        author_name, created_at, push_date, push_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    news_data.get("id"),
                    news_data.get("post_id"),
                    news_data.get("title"),
                    news_data.get("summary"),
                    news_data.get("category"),
                    news_data.get("importance_score", 0),
                    news_data.get("author_name"),
                    news_data.get("created_at"),
                    news_data.get("push_date"),
                    news_data.get("push_type")
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving news item: {e}")
            return False
    
    async def save_push_record(self, record_data: Dict[str, Any]) -> bool:
        """保存推送记录"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO push_records (
                        id, push_type, push_date, news_count, danger_count, success, error_message, pushed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record_data.get("id"),
                    record_data.get("push_type"),
                    record_data.get("push_date"),
                    record_data.get("news_count", 0),
                    record_data.get("danger_count", 0),
                    1 if record_data.get("success") else 0,
                    record_data.get("error_message"),
                    record_data.get("pushed_at")
                ))
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving push record: {e}")
            return False
    
    async def get_unanalyzed_posts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取未分析的帖子"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM posts 
                WHERE analyzed = 0 AND content IS NOT NULL AND length(content) >= 20
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_unanalyzed_agents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取未分析的成员"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM agents 
                WHERE analyzed = 0
                ORDER BY karma DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_top_news(
        self, 
        category: Optional[str] = None, 
        limit: int = 10,
        date: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取 Top 新闻
        
        Args:
            category: 分类
            limit: 数量限制
            date: 日期
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM posts WHERE is_top_news = 1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if date:
                query += " AND date(created_at) = ?"
                params.append(date)
            
            if start_time:
                query += " AND created_at >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND created_at <= ?"
                params.append(end_time)
            
            query += " ORDER BY importance_score DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_dangerous_posts(
        self,
        min_score: int = 8,
        limit: int = 20,
        date: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取危险言论
        
        Args:
            min_score: 最低危险分数
            limit: 数量限制
            date: 日期
            start_time: 开始时间 (ISO格式)
            end_time: 结束时间 (ISO格式)
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM dangerous_posts WHERE danger_score >= ?"
            params = [min_score]
            
            if date:
                query += " AND date(created_at) = ?"
                params.append(date)
            
            if start_time:
                query += " AND created_at >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND created_at <= ?"
                params.append(end_time)
            
            query += " ORDER BY danger_score DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_key_persons(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取关键人物"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM agents 
                WHERE is_key_person = 1
                ORDER BY influence_score DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_dangerous_agents(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取发布危险言论的成员"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM agents 
                WHERE danger_post_count > 0
                ORDER BY danger_post_count DESC
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_stats(self, date: Optional[str] = None) -> Dict[str, int]:
        """获取统计数据"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            stats["total_posts"] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM posts WHERE analyzed = 1")
            stats["analyzed_posts"] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            stats["total_agents"] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM agents WHERE is_key_person = 1")
            stats["key_persons"] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM posts WHERE is_top_news = 1")
            stats["top_news"] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM interactions")
            stats["interactions"] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM dangerous_posts")
            stats["dangerous_posts"] = (await cursor.fetchone())[0]
            
            cursor = await db.execute("SELECT COUNT(*) FROM agents WHERE danger_post_count > 0")
            stats["dangerous_agents"] = (await cursor.fetchone())[0]
            
            if date:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM dangerous_posts WHERE date(created_at) = ?",
                    (date,)
                )
                stats["today_dangerous"] = (await cursor.fetchone())[0]
            
            return stats
    
    async def post_exists(self, post_id: str) -> bool:
        """检查帖子是否存在"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,))
            return await cursor.fetchone() is not None
    
    async def agent_exists(self, agent_id: str) -> bool:
        """检查成员是否存在"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT 1 FROM agents WHERE id = ?", (agent_id,))
            return await cursor.fetchone() is not None
    
    async def get_push_records(
        self, 
        limit: int = 30,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取推送记录列表
        
        Args:
            limit: 数量限制
            date: 日期筛选
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM push_records WHERE success = 1"
            params = []
            
            if date:
                query += " AND push_date = ?"
                params.append(date)
            
            query += " ORDER BY pushed_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_push_record_by_id(self, push_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取推送记录
        
        Args:
            push_id: 推送记录ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM push_records WHERE id = ?",
                (push_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_all_agents(
        self, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取所有成员
        
        Args:
            limit: 数量限制
            offset: 偏移量
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM agents 
                ORDER BY influence_score DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


db = Database()
