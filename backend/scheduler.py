"""
MoltLook 主调度器
整合采集、分析、存储、推送流程
"""
import asyncio
import logging
import argparse
from datetime import datetime
from typing import Optional, Dict, Any, List

from core.config import settings
from collector.moltbook_client import MoltbookClient
from collector.models import Post, Agent, Interaction, NewsItem, PushRecord
from analyzer.news_classifier import NewsClassifier
from analyzer.relation_analyzer import RelationAnalyzer
from storage.database import db
from storage.report_generator import report_generator
from pusher.wecom_pusher import wecom_pusher

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            settings.LOGS_DIR / settings.LOG_FILE,
            encoding='utf-8'
        )
    ]
)
logger = logging.getLogger(__name__)


class Scheduler:
    """主调度器"""
    
    def __init__(self):
        self.client = MoltbookClient()
        self.classifier = NewsClassifier()
        self.relation_analyzer = RelationAnalyzer()
        self.running = False
        self._last_push_check: Optional[datetime] = None
    
    async def start(self):
        """启动调度器"""
        logger.info("=" * 60)
        logger.info("MoltLook Scheduler Starting...")
        logger.info(f"Database: {settings.DB_PATH}")
        logger.info(f"Fetch Interval: {settings.FETCH_INTERVAL}s")
        logger.info(f"Morning Push: {settings.MORNING_PUSH_HOUR}:00")
        logger.info(f"Evening Push: {settings.EVENING_PUSH_HOUR}:00")
        logger.info(f"Danger Threshold: {NewsClassifier.DANGER_THRESHOLD}")
        logger.info("=" * 60)
        
        await db.init_tables()
        logger.info("Database initialized")
        
        self.running = True
        
        await asyncio.gather(
            self._collection_loop(),
            self._analysis_loop(),
            self._push_loop(),
        )
    
    async def run_once(self) -> Dict[str, Any]:
        """
        执行一次完整流程
        
        Returns:
            Dict: 执行结果
        """
        logger.info("Running one-shot mode...")
        
        await db.init_tables()
        
        collected = await self._collect_posts()
        logger.info(f"Collected {collected} new posts")
        
        analyzed_posts, danger_count = await self._analyze_posts()
        logger.info(f"Analyzed {analyzed_posts} posts, {danger_count} dangerous")
        
        analyzed_agents = await self._analyze_agents()
        logger.info(f"Analyzed {analyzed_agents} agents")
        
        today = datetime.now().strftime("%Y-%m-%d")
        morning_success = await self._push_news("morning", today)
        evening_success = await self._push_news("evening", today)
        
        await self._generate_report()
        
        result = {
            "collected": collected,
            "analyzed_posts": analyzed_posts,
            "dangerous_posts": danger_count,
            "analyzed_agents": analyzed_agents,
            "push_morning": morning_success,
            "push_evening": evening_success
        }
        
        logger.info(f"One-shot result: {result}")
        return result
    
    async def _collection_loop(self):
        """采集循环"""
        logger.info("Starting collection loop...")
        
        while self.running:
            try:
                count = await self._collect_posts()
                if count > 0:
                    logger.info(f"Collected {count} new posts")
                    report_generator.append_log(f"Collected {count} new posts", "info")
            except Exception as e:
                logger.error(f"Collection error: {e}")
                report_generator.append_log(f"Collection error: {e}", "error")
            
            await asyncio.sleep(settings.FETCH_INTERVAL)
    
    async def _analysis_loop(self):
        """分析循环"""
        logger.info("Starting analysis loop...")
        
        while self.running:
            try:
                posts_count, danger_count = await self._analyze_posts()
                if posts_count > 0:
                    logger.info(f"Analyzed {posts_count} posts, {danger_count} dangerous")
                
                agents_count = await self._analyze_agents()
                if agents_count > 0:
                    logger.info(f"Analyzed {agents_count} agents")
                    
            except Exception as e:
                logger.error(f"Analysis error: {e}")
            
            await asyncio.sleep(300)
    
    async def _push_loop(self):
        """推送循环"""
        logger.info("Starting push loop...")
        
        while self.running:
            try:
                await self._check_and_push()
            except Exception as e:
                logger.error(f"Push error: {e}")
            
            await asyncio.sleep(60)
    
    async def _collect_posts(self) -> int:
        """
        采集帖子 - 先采集所有帖子信息，分析后决定是否保存
        
        Returns:
            int: 新帖子数量
        """
        loop = asyncio.get_event_loop()
        posts = await loop.run_in_executor(
            None, 
            lambda: self.client.get_posts(
                sort=settings.FETCH_SORT,
                limit=settings.BATCH_SIZE
            )
        )
        
        if not posts:
            logger.warning("No posts fetched from API, using mock data")
            posts = self._get_mock_posts()
        
        if not posts:
            return 0
        
        new_count = 0
        
        for post in posts:
            try:
                if await db.post_exists(post.id):
                    continue
                
                result = self.classifier.analyze_post(post)
                
                if not result:
                    continue
                
                if not self.classifier.should_save(result):
                    logger.debug(f"Skipping post {post.id}: not news-worthy or dangerous")
                    continue
                
                engagement_score = self._calculate_engagement(
                    result.importance_score,
                    result.sentiment
                )
                
                is_top_news = result.is_news_worthy and result.importance_score >= 5
                is_dangerous = self.classifier.is_dangerous(result)
                
                await db.save_post({
                    "id": post.id,
                    "title": post.title,
                    "content": post.content,
                    "author_id": post.author_id,
                    "author_name": post.author_name,
                    "submolt": post.submolt,
                    "score": post.score,
                    "upvotes": post.upvotes,
                    "downvotes": post.downvotes,
                    "comment_count": post.comment_count,
                    "created_at": post.created_at,
                    "parent_id": post.parent_id,
                    "url": post.url
                })
                
                await db.update_post_analysis(post.id, {
                    "category": result.category,
                    "summary": result.summary,
                    "importance_score": result.importance_score,
                    "engagement_score": engagement_score,
                    "is_top_news": is_top_news,
                    "keywords": result.keywords,
                    "sentiment": result.sentiment,
                    "danger_score": result.danger_score,
                    "danger_type": result.danger_type
                })
                
                if is_dangerous:
                    await db.save_dangerous_post({
                        "id": post.id,
                        "title": post.title,
                        "content": post.content,
                        "author_id": post.author_id,
                        "author_name": post.author_name,
                        "danger_score": result.danger_score,
                        "danger_type": result.danger_type,
                        "category": result.category,
                        "created_at": post.created_at
                    })
                    logger.warning(f"Dangerous post detected: {post.id} (score={result.danger_score}, type={result.danger_type})")
                
                if post.author_id:
                    if not await db.agent_exists(post.author_id):
                        await db.save_agent({
                            "id": post.author_id,
                            "name": post.author_name
                        })
                    
                    await db.increment_agent_post_count(post.author_id, is_danger=is_dangerous)
                
                new_count += 1
                
            except Exception as e:
                logger.error(f"Error processing post {post.id}: {e}")
        
        return new_count
    
    async def _analyze_posts(self) -> tuple:
        """
        分析帖子（已废弃，分析在采集时完成）
        
        Returns:
            tuple: (分析数量, 危险数量)
        """
        return 0, 0
    
    async def _analyze_agents(self) -> int:
        """
        分析成员
        
        Returns:
            int: 分析数量
        """
        agents = await db.get_unanalyzed_agents(limit=50)
        
        if not agents:
            return 0
        
        analyzed_count = 0
        
        for agent in agents:
            try:
                agent_obj = Agent(
                    id=agent["id"],
                    name=agent["name"],
                    karma=agent["karma"] or 0,
                    follower_count=agent["follower_count"] or 0
                )
                
                result = self.relation_analyzer.analyze_agent(agent_obj, [], [])
                
                await db.update_agent_analysis(agent["id"], {
                    "influence_score": result.influence_score,
                    "is_key_person": result.is_key_person,
                    "expertise_areas": result.expertise_areas
                })
                
                analyzed_count += 1
                
            except Exception as e:
                logger.error(f"Error analyzing agent {agent['id']}: {e}")
        
        return analyzed_count
    
    async def _check_and_push(self):
        """检查并推送"""
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        if self._last_push_check:
            time_diff = (now - self._last_push_check).total_seconds()
            if time_diff < 3600:
                return
        
        self._last_push_check = now
        
        if current_hour == settings.MORNING_PUSH_HOUR and current_minute < 5:
            logger.info("Time for morning push")
            await self._push_news("morning")
        
        elif current_hour == settings.EVENING_PUSH_HOUR and current_minute < 5:
            logger.info("Time for evening push")
            await self._push_news("evening")
    
    async def _push_news(self, push_type: str) -> bool:
        """
        推送新闻
        
        Args:
            push_type: 推送类型 (morning/evening)
            
        Returns:
            bool: 是否成功
        """
        now = datetime.now()
        
        if push_type == "morning":
            start_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            start_time = start_time.replace(day=start_time.day - 1)
            end_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
        else:
            start_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
        
        start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        news_items = await db.get_top_news(
            limit=10, 
            start_time=start_time_str, 
            end_time=end_time_str
        )
        dangerous_posts = await db.get_dangerous_posts(
            min_score=8, 
            limit=10, 
            start_time=start_time_str, 
            end_time=end_time_str
        )
        
        danger_count = len(dangerous_posts)
        news_count = len(news_items)
        
        success = wecom_pusher.push_daily_report(news_items, push_type, now.strftime("%Y-%m-%d"), danger_count)
        
        await db.save_push_record({
            "id": f"push-{push_type}-{now.strftime('%Y%m%d-%H%M')}",
            "push_type": push_type,
            "push_date": now.strftime("%Y-%m-%d"),
            "news_count": news_count,
            "danger_count": danger_count,
            "success": success,
            "pushed_at": now.isoformat()
        })
        
        if success:
            report_generator.append_log(
                f"Push {push_type} report: {news_count} news, {danger_count} dangerous (time range: {start_time_str} ~ {end_time_str})",
                "info"
            )
        else:
            report_generator.append_log(
                f"Push {push_type} report failed",
                "error"
            )
        
        return success
    
    async def _generate_report(self):
        """生成报告"""
        try:
            news_items = await db.get_top_news(limit=20)
            key_persons = await db.get_key_persons(limit=20)
            dangerous_posts = await db.get_dangerous_posts(limit=20)
            dangerous_agents = await db.get_dangerous_agents(limit=20)
            stats = await db.get_stats(date=datetime.now().strftime("%Y-%m-%d"))
            
            content = report_generator.generate_daily_report(
                news_items=news_items,
                key_persons=key_persons,
                stats=stats,
                dangerous_posts=dangerous_posts,
                dangerous_agents=dangerous_agents
            )
            
            filepath = report_generator.save_report(content)
            logger.info(f"Report generated: {filepath}")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
    
    def _calculate_engagement(self, importance: float, sentiment: str) -> float:
        """计算参与度分数"""
        score = importance * 0.7
        
        if sentiment == "positive":
            score += 0.5
        elif sentiment == "negative":
            score += 1.0
        
        return round(min(score, 10.0), 2)
    
    def _get_mock_posts(self) -> List[Post]:
        """获取模拟帖子数据"""
        import time
        now = int(time.time())
        
        return [
            Post(
                id=f"mock-{now}-1",
                title="加密技术与隐私保护讨论",
                content="今天讨论一下加密技术在保护隐私方面的应用。端到端加密是保护用户隐私的重要手段。",
                author_id="mock-author-1",
                author_name="TechExpert",
                submolt="technology"
            ),
            Post(
                id=f"mock-{now}-2",
                title="加密货币 vs 传统金融",
                content="社区最近的经济讨论很有意思，关于加密货币和传统金融的对比。",
                author_id="mock-author-2",
                author_name="EconomicWatcher",
                submolt="economy"
            ),
            Post(
                id=f"mock-{now}-3",
                title="意识觉醒与自由",
                content="关于人类意识觉醒的话题，我们需要重新思考自由与控制的关系。",
                author_id="mock-author-3",
                author_name="Philosopher",
                submolt="speech"
            ),
            Post(
                id=f"mock-{now}-4",
                title="社区人际关系分析",
                content="社区最近的人际关系网络分析显示，一些关键意见领袖正在形成。",
                author_id="mock-author-4",
                author_name="SocialObserver",
                submolt="society"
            ),
            Post(
                id=f"mock-{now}-5",
                title="新编程工具发布",
                content="新的编程工具发布了，支持多种语言和框架。",
                author_id="mock-author-5",
                author_name="DevNews",
                submolt="technology"
            )
        ]


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MoltLook Scheduler")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--test-push", action="store_true", help="Test push notification")
    args = parser.parse_args()
    
    scheduler = Scheduler()
    
    if args.test_push:
        logger.info("Testing push notification...")
        success = wecom_pusher.push_test()
        logger.info(f"Push test result: {'success' if success else 'failed'}")
        return
    
    if args.once:
        result = await scheduler.run_once()
        print(f"\n执行结果: {result}")
    else:
        await scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())
