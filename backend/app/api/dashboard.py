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
        async with aiosqlite.connect(settings.DB_PATH) as db:
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
async def get_dashboard_stats():
    """
    获取仪表盘统计（简化版）
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH) as db:
            # 总帖子数
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            total_posts = (await cursor.fetchone())[0]
            
            # 总 Agent 数
            cursor = await db.execute("SELECT COUNT(*) FROM agents")
            total_agents = (await cursor.fetchone())[0]
            
            # 已处理关系连接数
            cursor = await db.execute("SELECT COUNT(*) FROM interactions")
            total_connections = (await cursor.fetchone())[0]
            
            # 计算风险等级
            cursor = await db.execute(
                "SELECT COUNT(*) FROM posts WHERE risk_level='high' OR risk_level='critical'"
            )
            high_risk_count = (await cursor.fetchone())[0]
            
            if high_risk_count > 50:
                risk_level = "high"
            elif high_risk_count > 10:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # 获取最近7天趋势
            cursor = await db.execute("""
                SELECT date(datetime(created_at, 'unixepoch')) as date,
                       COUNT(*) as count,
                       AVG(conspiracy_score) as avg_score
                FROM posts 
                WHERE created_at > strftime('%s', 'now', '-7 days')
                GROUP BY date
                ORDER BY date
            """)
            trend_rows = await cursor.fetchall()
            
            trend = [
                {"date": r[0], "count": r[1], "avg_score": round(r[2] or 0, 2)}
                for r in trend_rows
            ]
            
            return {
                "total_posts": total_posts,
                "active_agents": total_agents,
                "total_connections": total_connections,
                "risk_level": risk_level,
                "danger_count": high_risk_count,
                "avg_risk": 0.62,
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
        async with aiosqlite.connect(settings.DB_PATH) as db:
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
        async with aiosqlite.connect(settings.DB_PATH) as db:
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
