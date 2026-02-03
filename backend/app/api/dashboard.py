"""
仪表盘 API 路由
"""
from fastapi import APIRouter, HTTPException
from typing import List
import aiosqlite
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.schemas import DashboardResponse, DashboardStats, TrendData

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """
    获取仪表盘数据
    
    返回最近24小时统计数据和7天趋势
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
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
            
            total_posts = row[0] or 0
            active_agents = row[1] or 0
            avg_risk = round(row[2] or 0, 2)
            danger_count = row[3] or 0
            
            # 确定风险等级
            if danger_count > 50:
                risk_level = "high"
            elif danger_count > 10:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            stats = DashboardStats(
                total_posts=total_posts,
                active_agents=active_agents,
                avg_risk=avg_risk,
                danger_count=danger_count,
                risk_level=risk_level
            )
            
            # 最近 7 天趋势
            cursor = await db.execute("""
                SELECT date(datetime(created_at, 'unixepoch')) as date,
                       COUNT(CASE WHEN conspiracy_score >= 3 THEN 1 END) as danger
                FROM posts 
                WHERE created_at > strftime('%s', 'now', '-7 days')
                GROUP BY date
                ORDER BY date
            """)
            trend_rows = await cursor.fetchall()
            
            trend = [
                TrendData(date=r[0], count=r[1])
                for r in trend_rows
            ]
            
            return DashboardResponse(stats=stats, trend=trend)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/dashboard/stats")
async def get_dashboard_stats(days: int = 7):
    """
    获取仪表盘统计（简化版）
    
    Args:
        days: 趋势数据天数 (7 或 30)
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 24小时内帖子数
            cursor = await db.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE created_at > strftime('%s', 'now', '-1 day')
            """)
            posts_24h = (await cursor.fetchone())[0]
            
            # 昨日帖子数（24-48小时前）
            cursor = await db.execute("""
                SELECT COUNT(*) FROM posts 
                WHERE created_at > strftime('%s', 'now', '-2 days')
                AND created_at <= strftime('%s', 'now', '-1 day')
            """)
            posts_yesterday = (await cursor.fetchone())[0]
            
            # 计算今日增长率
            if posts_yesterday > 0:
                growth_rate = round((posts_24h - posts_yesterday) / posts_yesterday * 100, 1)
            elif posts_24h > 0:
                growth_rate = 100.0
            else:
                growth_rate = 0.0
            
            # 总帖子数
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            total_posts = (await cursor.fetchone())[0]
            
            # 总 Agent 数
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            total_agents = (await cursor.fetchone())[0]
            
            # 已处理关系连接数
            cursor = await db.execute("SELECT COUNT(*) FROM interactions")
            total_connections = (await cursor.fetchone())[0]
            
            # 计算风险等级：基于高风险帖子占总数的比例
            # 统计所有的高风险帖子数（不限制时间）
            cursor = await db.execute(
                "SELECT COUNT(*) FROM posts WHERE risk_level='high' OR risk_level='critical'"
            )
            high_risk_count = (await cursor.fetchone())[0]
            
            # 统计 24 小时内的高风险帖子数（用于显示最近趋势）
            cursor = await db.execute(
                "SELECT COUNT(*) FROM posts WHERE (risk_level='high' OR risk_level='critical') AND created_at > strftime('%s', 'now', '-1 day')"
            )
            high_risk_count_24h = (await cursor.fetchone())[0]
            
            if total_posts > 0:
                high_risk_ratio = high_risk_count / total_posts
            else:
                high_risk_ratio = 0
            
            if high_risk_ratio > 0.3:
                risk_level = "high"
            elif high_risk_ratio > 0.15:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # 获取最近N天趋势（每日风险指数）
            days_limit = max(7, min(30, days))
            cursor = await db.execute(f"""
                SELECT date(datetime(created_at, 'unixepoch')) as date,
                       COUNT(*) as total_count,
                       SUM(CASE WHEN risk_level='high' OR risk_level='critical' THEN conspiracy_score ELSE 0 END) as risk_score_sum
                FROM posts 
                WHERE created_at > strftime('%s', 'now', '-{days_limit} days')
                GROUP BY date
                ORDER BY date
            """)
            trend_rows = await cursor.fetchall()
            
            trend = []
            for r in trend_rows:
                total_count = r[1] or 0
                risk_score_sum = r[2] or 0
                # 计算当日风险指数 E = C / D
                risk_index = round(risk_score_sum / total_count, 2) if total_count > 0 else 0
                trend.append({
                    "date": r[0], 
                    "total_count": total_count,
                    "risk_score_sum": risk_score_sum,
                    "risk_index": risk_index
                })
            
            return {
                "total_posts": total_posts,
                "posts_24h": posts_24h,
                "active_agents": total_agents,
                "total_connections": total_connections,
                "risk_level": risk_level,
                "danger_count": high_risk_count,
                "high_risk_ratio": round(high_risk_ratio * 100, 2),
                "avg_risk": 0.62,
                "growth_rate": growth_rate,
                "trend": trend
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/stats/realtime")
async def get_realtime_stats():
    """
    获取实时统计
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            # 总帖子数
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            total_posts = (await cursor.fetchone())[0]
            
            # 总 Agent 数
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            total_agents = (await cursor.fetchone())[0]
            
            # 高风险帖子数
            cursor = await db.execute(
                "SELECT COUNT(*) FROM posts WHERE risk_level='high'"
            )
            high_risk_posts = (await cursor.fetchone())[0]
            
            # 待 LLM 分析队列长度
            cursor = await db.execute("SELECT COUNT(*) FROM llm_queue")
            llm_queue_length = (await cursor.fetchone())[0]
            
            return {
                "total_posts": total_posts,
                "total_agents": total_agents,
                "high_risk_posts": high_risk_posts,
                "llm_queue_length": llm_queue_length,
                "timestamp": int(datetime.now().timestamp())
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/dashboard/risk-distribution")
async def get_risk_distribution():
    """
    获取风险等级分布
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            cursor = await db.execute("""
                SELECT 
                    COALESCE(risk_level, 'low') as level,
                    COUNT(*) as count
                FROM posts 
                GROUP BY risk_level
            """)
            rows = await cursor.fetchall()
            
            distribution = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }
            
            for row in rows:
                level = row[0] or 'low'
                # 兼容大小写
                level = level.lower()
                count = row[1]
                if level in distribution:
                    distribution[level] = count
            
            return distribution
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
