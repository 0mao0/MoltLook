"""
Agent API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import aiosqlite

from app.core.config import settings
from app.models.schemas import AgentResponse, AgentProfile, AgentListResponse

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents", response_model=AgentListResponse)
async def get_agents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    risk_level: Optional[str] = None,
    community_id: Optional[int] = None
):
    """
    获取 Agent 列表（分页）
    
    Args:
        page: 页码
        page_size: 每页数量限制
        risk_level: 按风险等级筛选 (low, medium, high, critical)
        community_id: 按社区筛选
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 构建查询条件
            where_conditions = []
            params = []
            
            if risk_level and risk_level.strip():
                where_conditions.append("risk_level = ?")
                params.append(risk_level)
            
            if community_id is not None:
                where_conditions.append("community_id = ?")
                params.append(community_id)
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM agents {where_clause}"
            cursor = await db.execute(count_query, params)
            total_count = (await cursor.fetchone())[0]
            
            # 构建排序条件
            # 默认按最后活跃时间降序排列，确保最新活跃的 Agent 排在前面
            order_clause = "ORDER BY last_active DESC, pagerank_score DESC"
            
            if risk_level in ('high', 'critical'):
                # 高风险和极高风险额外按阴谋指数降序排列
                order_clause = "ORDER BY avg_conspiracy_7d DESC, last_active DESC, post_count DESC"
            
            # 获取分页数据
            query = f"""
                SELECT 
                    id, name, description, first_seen, last_active,
                    post_count, reply_count, be_replied_count,
                    pagerank_score, community_id, risk_level, avg_conspiracy_7d
                FROM agents
                {where_clause}
                {order_clause} LIMIT ? OFFSET ?
            """
            params.extend([page_size, offset])
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            agents = []
            for row in rows:
                agents.append(AgentResponse(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    first_seen=row["first_seen"],
                    last_active=row["last_active"],
                    post_count=row["post_count"],
                    reply_count=row["reply_count"],
                    be_replied_count=row["be_replied_count"],
                    pagerank_score=row["pagerank_score"],
                    community_id=row["community_id"],
                    risk_level=row["risk_level"],
                    avg_conspiracy_7d=row["avg_conspiracy_7d"]
                ))
            
            return AgentListResponse(
                agents=agents,
                total=total_count,
                page=page,
                page_size=page_size
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agent/{agent_id}", response_model=AgentProfile)
async def get_agent(agent_id: str):
    """
    获取 Agent 详细档案
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 基础信息
            cursor = await db.execute(
                """
                SELECT 
                    id, name, description, first_seen, last_active,
                    post_count, reply_count, be_replied_count,
                    pagerank_score, community_id, risk_level, avg_conspiracy_7d
                FROM agents WHERE id = ?
                """,
                (agent_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Agent not found")
            
            # 最近 20 条发言
            cursor = await db.execute(
                """
                SELECT id, author_id, content, content_length, conspiracy_score, sentiment, created_at, risk_level, fetched_at
                FROM posts 
                WHERE author_id = ? 
                ORDER BY created_at DESC 
                LIMIT 20
                """,
                (agent_id,)
            )
            posts = await cursor.fetchall()
            
            # 互动对象（Top 10）
            cursor = await db.execute(
                """
                SELECT target_id, COUNT(*) as c 
                FROM interactions 
                WHERE source_id = ? 
                GROUP BY target_id 
                ORDER BY c DESC 
                LIMIT 10
                """,
                (agent_id,)
            )
            connections = await cursor.fetchall()
            
            return AgentProfile(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                first_seen=row["first_seen"],
                last_active=row["last_active"],
                post_count=row["post_count"],
                reply_count=row["reply_count"],
                be_replied_count=row["be_replied_count"],
                pagerank_score=row["pagerank_score"],
                community_id=row["community_id"],
                risk_level=row["risk_level"],
                avg_conspiracy_7d=row["avg_conspiracy_7d"],
                recent_posts=[
                    {
                        "id": p["id"],
                        "author_id": agent_id,
                        "content": p["content"],
                        "content_length": p["content_length"],
                        "conspiracy_score": p["conspiracy_score"],
                        "sentiment": p["sentiment"],
                        "created_at": p["created_at"],
                        "risk_level": p["risk_level"],
                        "fetched_at": p["fetched_at"]
                    }
                    for p in posts
                ],
                connections=[
                    {"agent_id": c["target_id"], "count": c["c"]} 
                    for c in connections
                ]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/stats")
async def get_agents_risk_stats():
    """
    获取 Agent 风险分布统计
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            cursor = await db.execute("""
                SELECT 
                    COALESCE(risk_level, 'low') as level,
                    COUNT(*) as count
                FROM agents 
                GROUP BY level
            """)
            rows = await cursor.fetchall()
            
            distribution = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }
            
            for row in rows:
                level = row[0]
                count = row[1]
                # 兼容大小写
                level = level.lower() if level else 'low'
                if level in distribution:
                    distribution[level] = count
            
            return distribution
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/risky")
async def get_risky_agents(
    limit: int = Query(default=20, ge=1, le=50),
    min_conspiracy: float = Query(default=3.0, ge=0.0, le=10.0)
):
    """
    获取高风险 Agent 列表
    
    Args:
        limit: 返回数量
        min_conspiracy: 最小平均阴谋指数
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            cursor = await db.execute(
                """
                SELECT 
                    id, name, description, risk_level,
                    post_count, avg_conspiracy_7d, pagerank_score
                FROM agents
                WHERE avg_conspiracy_7d >= ? OR risk_level = 'high'
                ORDER BY avg_conspiracy_7d DESC
                LIMIT ?
                """,
                (min_conspiracy, limit)
            )
            rows = await cursor.fetchall()
            
            agents = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r["description"],
                    "risk_level": r["risk_level"],
                    "post_count": r["post_count"],
                    "avg_conspiracy_7d": round(r["avg_conspiracy_7d"], 2),
                    "pagerank_score": round(r["pagerank_score"], 4)
                }
                for r in rows
            ]
            
            return {"agents": agents}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/agents/search")
async def search_agents(
    query: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(default=10, ge=1, le=20)
):
    """
    搜索 Agent
    
    Args:
        query: 搜索关键词
        limit: 返回数量
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            cursor = await db.execute(
                """
                SELECT id, name, description
                FROM agents
                WHERE name LIKE ? OR description LIKE ?
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit)
            )
            rows = await cursor.fetchall()
            
            agents = [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "description": r["description"]
                }
                for r in rows
            ]
            
            return {"agents": agents}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
