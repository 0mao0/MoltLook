"""
MoltLook 采集引擎
独立运行，负责从 Moltbook API 采集数据
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

import aiohttp
import aiosqlite

from app.core.config import settings
from app.services.moltbook_api import MoltbookAPI
from app.services.feature_extractor import feature_extractor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Collector:
    """数据采集器"""
    
    def __init__(self):
        self.api = MoltbookAPI()
        self.db_path = settings.DB_PATH
        self.running = False
    
    async def init_db(self):
        """初始化数据库"""
        async with aiosqlite.connect(self.db_path, timeout=30) as db:
            # 启用 WAL 模式
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute("PRAGMA busy_timeout = 5000;")
            await db.commit()
            logger.info("Database initialized")
    
    async def get_collection_state(self, db: aiosqlite.Connection) -> Dict[str, Any]:
        """获取采集状态"""
        cursor = await db.execute(
            "SELECT last_seen_id, last_fetch_time, total_posts FROM collection_state WHERE id = 1"
        )
        row = await cursor.fetchone()
        if row:
            return {
                "last_seen_id": row[0],
                "last_fetch_time": row[1],
                "total_posts": row[2]
            }
        return {"last_seen_id": None, "last_fetch_time": 0, "total_posts": 0}
    
    async def update_collection_state(
        self, 
        db: aiosqlite.Connection, 
        last_seen_id: Optional[str] = None,
        total_posts: int = None
    ):
        """更新采集状态"""
        if last_seen_id:
            await db.execute(
                "UPDATE collection_state SET last_seen_id = ?, last_fetch_time = ? WHERE id = 1",
                (last_seen_id, int(time.time()))
            )
        if total_posts is not None:
            await db.execute(
                "UPDATE collection_state SET total_posts = ? WHERE id = 1",
                (total_posts,)
            )
        await db.commit()
    
    async def save_post(self, db: aiosqlite.Connection, post_data: dict) -> bool:
        """
        保存帖子到数据库
        
        Returns:
            bool: 是否为新帖子
        """
        # 检查是否已存在
        cursor = await db.execute(
            "SELECT id FROM posts WHERE id = ?",
            (post_data["id"],)
        )
        if await cursor.fetchone():
            return False
        
        # 确保有 URL 和标题
        url = post_data.get("url")
        if not url:
            # 修正 URL 格式：从 posts/ 改为 post/
            url = f"https://www.moltbook.com/post/{post_data['id']}"
            
        title = post_data.get("title")
        if not title:
            # 如果没标题，取内容前 30 个字符
            content = post_data.get("content", "")
            title = (content[:30] + "...") if len(content) > 30 else content
            if not title:
                title = "查看详情"

        # 插入帖子
        await db.execute(
            """
            INSERT INTO posts (
                id, author_id, content, content_length, parent_id, submolt,
                created_at, fetched_at, conspiracy_score, sentiment,
                llm_analyzed, intent, risk_level, summary, url, title
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_data["id"],
                post_data["author_id"],
                post_data["content"],
                post_data["content_length"],
                post_data.get("parent_id"),
                post_data["submolt"],
                post_data["created_at"],
                post_data["fetched_at"],
                post_data["conspiracy_score"],
                post_data["sentiment"],
                post_data["llm_analyzed"],
                post_data["intent"],
                post_data["risk_level"],
                post_data["summary"],
                url,
                title
            )
        )
        
        # 如果阴谋指数 >= 2，加入 LLM 分析队列
        if post_data["conspiracy_score"] >= 2:
            await db.execute(
                """
                INSERT OR IGNORE INTO llm_queue (post_id, content_snippet, priority, added_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    post_data["id"],
                    post_data["content"][:300],
                    post_data["conspiracy_score"],
                    int(time.time())
                )
            )
        
        # 更新或创建 Agent
        await db.execute(
            """
            INSERT INTO agents (id, name, first_seen, last_active, post_count)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
                name = CASE 
                    WHEN name IS NULL OR name = id OR name = 'unknown' THEN excluded.name 
                    ELSE name 
                END,
                last_active = excluded.last_active,
                post_count = post_count + 1
            """,
            (
                post_data["author_id"],
                post_data.get("author_name") or post_data["author_id"],
                post_data["created_at"],
                post_data["created_at"]
            )
        )
        
        return True
    
    async def save_interaction(
        self, 
        db: aiosqlite.Connection, 
        source_id: str, 
        target_id: str, 
        post_id: str,
        created_at: int
    ):
        """保存互动关系"""
        try:
            await db.execute(
                """
                INSERT OR IGNORE INTO interactions (source_id, target_id, post_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (source_id, target_id, post_id, created_at)
            )
            
            # 更新 Agent 的互动计数
            await db.execute(
                "UPDATE agents SET reply_count = reply_count + 1 WHERE id = ?",
                (source_id,)
            )
            await db.execute(
                "UPDATE agents SET be_replied_count = be_replied_count + 1 WHERE id = ?",
                (target_id,)
            )
            
        except Exception as e:
            logger.error(f"Error saving interaction: {e}")

    async def cleanup_low_medium_posts(self, db: aiosqlite.Connection):
        """
        清理中低风险帖子，仅保留最新 1000 条
        """
        try:
            await db.execute(
                """
                DELETE FROM posts
                WHERE id IN (
                    SELECT id FROM posts
                    WHERE COALESCE(risk_level, 'low') IN ('low', 'medium')
                    ORDER BY created_at DESC
                    LIMIT -1 OFFSET 1000
                )
                """
            )
        except Exception as e:
            logger.error(f"Error cleaning low/medium posts: {e}")
    
    async def process_posts(self, posts: List[dict]) -> int:
        """
        处理帖子列表
        
        Returns:
            int: 新帖子数量
        """
        new_count = 0
        
        async with aiosqlite.connect(self.db_path, timeout=30) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            for post in posts:
                try:
                    # 提取特征
                    features = feature_extractor.extract_features(post)
                    
                    # 保存帖子
                    is_new = await self.save_post(db, features)
                    
                    if is_new:
                        new_count += 1
                        
                        # 如果是回复，保存互动关系
                        if features.get("parent_id"):
                            # 获取父帖作者
                            cursor = await db.execute(
                                "SELECT author_id FROM posts WHERE id = ?",
                                (features["parent_id"],)
                            )
                            parent_row = await cursor.fetchone()
                            
                            if parent_row:
                                await self.save_interaction(
                                    db,
                                    features["author_id"],
                                    parent_row[0],
                                    features["id"],
                                    features["created_at"]
                                )
                            else:
                                # 父帖不在数据库中，可能是之前采集的
                                logger.debug(f"Parent post not found: {features['parent_id']}")
                    
                except Exception as e:
                    logger.error(f"Error processing post {post.get('id')}: {e}")
                    continue
            
            if new_count > 0:
                await self.cleanup_low_medium_posts(db)
        
        return new_count
    
    async def collection_task(self):
        """采集任务 - 60秒循环"""
        logger.info("Starting collection task...")
        
        while self.running:
            try:
                # 获取采集状态
                async with aiosqlite.connect(self.db_path, timeout=30) as db:
                    state = await self.get_collection_state(db)
                
                last_seen_id = state["last_seen_id"]
                
                # 获取帖子
                posts = await self.api.get_posts(
                    sort="new",
                    limit=settings.BATCH_SIZE,
                    after=last_seen_id
                )
                
                if posts:
                    logger.info(f"Fetched {len(posts)} posts")
                    
                    # 处理帖子
                    new_count = await self.process_posts(posts)
                    logger.info(f"Saved {new_count} new posts")
                    
                    # 更新采集状态
                    last_post_id = posts[-1].get("id")
                    async with aiosqlite.connect(self.db_path, timeout=30) as db:
                        await self.update_collection_state(
                            db, 
                            last_seen_id=last_post_id,
                            total_posts=state["total_posts"] + new_count
                        )
                else:
                    logger.debug("No new posts")
                
            except Exception as e:
                logger.error(f"Collection error: {e}")
            
            # 等待 60 秒
            await asyncio.sleep(settings.FETCH_INTERVAL)
    
    async def status_check_task(self):
        """状态检查任务 - 4小时循环"""
        logger.info("Starting status check task...")
        
        while self.running:
            try:
                status = await self.api.get_agent_status()
                
                if status:
                    agent_status = status.get("status", "unknown")
                    logger.info(f"Agent status: {agent_status}")
                    
                    if agent_status == "claimed":
                        logger.info("✅ Agent is claimed and active")
                    else:
                        logger.warning(f"⏳ Agent status: {agent_status}")
                else:
                    logger.error("Failed to get agent status")
                    
            except Exception as e:
                logger.error(f"Status check error: {e}")
            
            # 等待 4 小时
            await asyncio.sleep(settings.STATUS_CHECK_INTERVAL)
    
    async def engagement_task(self):
        """发帖任务 - 4.5小时循环"""
        logger.info("Starting engagement task...")
        
        # 首次延迟 30 分钟
        await asyncio.sleep(1800)
        
        while self.running:
            try:
                # 生成观察报告
                content = await self.generate_observation_post()
                
                if content:
                    result = await self.api.create_post(
                        content=content,
                        submolt="general"
                    )
                    
                    if result:
                        logger.info("Posted observation report")
                    else:
                        logger.warning("Failed to post observation report")
                
            except Exception as e:
                logger.error(f"Engagement error: {e}")
            
            # 等待 4.5 小时
            await asyncio.sleep(settings.POST_INTERVAL)
    
    async def generate_observation_post(self) -> Optional[str]:
        """生成观察报告帖子"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 获取最近统计
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM posts WHERE created_at > strftime('%s', 'now', '-1 hour')"
                )
                posts_last_hour = (await cursor.fetchone())[0]
                
                cursor = await db.execute(
                    "SELECT COUNT(DISTINCT author_id) FROM posts WHERE created_at > strftime('%s', 'now', '-1 day')"
                )
                active_agents = (await cursor.fetchone())[0]
                
                cursor = await db.execute(
                    "SELECT AVG(conspiracy_score) FROM posts WHERE created_at > strftime('%s', 'now', '-1 day')"
                )
                avg_conspiracy = (await cursor.fetchone())[0] or 0
                
                content = f"""🔍 MoltLook Observation Report

📊 Last Hour: {posts_last_hour} posts
👥 Active Agents (24h): {active_agents}
⚠️ Avg Conspiracy Score: {avg_conspiracy:.2f}/10

Monitoring the network... 🦞"""
                
                return content
                
        except Exception as e:
            logger.error(f"Error generating observation post: {e}")
            return None
    
    async def run(self):
        """运行采集器"""
        logger.info("=" * 60)
        logger.info("MoltLook Collector Starting...")
        logger.info(f"Agent: {settings.AGENT_NAME}")
        logger.info(f"Database: {self.db_path}")
        logger.info("=" * 60)
        
        # 初始化数据库
        await self.init_db()
        
        self.running = True
        
        # 启动三个任务
        await asyncio.gather(
            self.collection_task(),
            self.status_check_task(),
            self.engagement_task()
        )
    
    def stop(self):
        """停止采集器"""
        logger.info("Stopping collector...")
        self.running = False


async def main():
    """主函数"""
    collector = Collector()
    
    try:
        await collector.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        collector.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        collector.stop()


if __name__ == "__main__":
    asyncio.run(main())
