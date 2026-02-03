"""
网络图 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import aiosqlite

from app.core.config import settings
from app.models.schemas import NetworkData

router = APIRouter(prefix="/api", tags=["network"])


@router.get("/network", response_model=NetworkData)
async def get_network(
    limit: int = Query(default=200, ge=50, le=500),
    community_id: int = Query(default=None)
):
    """
    获取关系网络数据
    
    Args:
        limit: 边的数量限制
        community_id: 筛选特定社区
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 构建查询
            query = """
                SELECT i.source_id, i.target_id, i.weight, i.created_at,
                       a1.community_id as s_comm, a2.community_id as t_comm,
                       a1.post_count as s_posts, a2.post_count as t_posts,
                       a1.name as s_name, a2.name as t_name
                FROM interactions i
                JOIN agents a1 ON i.source_id = a1.id
                JOIN agents a2 ON i.target_id = a2.id
            """
            params = []
            
            if community_id is not None:
                query += " WHERE a1.community_id = ? AND a2.community_id = ?"
                params = [community_id, community_id]
            
            query += " ORDER BY i.created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            edges = []
            nodes_dict = {}
            
            for row in rows:
                source = row["source_id"]
                target = row["target_id"]
                weight = row["weight"]
                
                edges.append({
                    "from": source,
                    "to": target,
                    "value": weight
                })
                
                # 添加节点（去重）
                if source not in nodes_dict:
                    nodes_dict[source] = {
                        "id": source,
                        "label": row["s_name"] or source[:8],
                        "group": row["s_comm"],
                        "value": row["s_posts"] or 1
                    }
                if target not in nodes_dict:
                    nodes_dict[target] = {
                        "id": target,
                        "label": row["t_name"] or target[:8],
                        "group": row["t_comm"],
                        "value": row["t_posts"] or 1
                    }
            
            return NetworkData(
                nodes=list(nodes_dict.values()),
                edges=edges
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/network/communities")
async def get_communities():
    """
    获取社区列表
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            cursor = await db.execute("""
                SELECT 
                    community_id,
                    COUNT(*) as agent_count,
                    AVG(pagerank_score) as avg_pagerank
                FROM agents
                WHERE community_id != -1
                GROUP BY community_id
                ORDER BY agent_count DESC
            """)
            rows = await cursor.fetchall()
            
            communities = [
                {
                    "id": row[0],
                    "agent_count": row[1],
                    "avg_pagerank": round(row[2], 4)
                }
                for row in rows
            ]
            
            return {"communities": communities}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/network/agent/{agent_id}/connections")
async def get_agent_connections(
    agent_id: str,
    limit: int = Query(default=20, ge=1, le=50)
):
    """
    获取特定 Agent 的连接
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 获取 outgoing connections（回复他人）
            cursor = await db.execute("""
                SELECT i.target_id as agent_id, a.name, COUNT(*) as count
                FROM interactions i
                JOIN agents a ON i.target_id = a.id
                WHERE i.source_id = ?
                GROUP BY i.target_id
                ORDER BY count DESC
                LIMIT ?
            """, (agent_id, limit))
            outgoing = await cursor.fetchall()
            
            # 获取 incoming connections（被回复）
            cursor = await db.execute("""
                SELECT i.source_id as agent_id, a.name, COUNT(*) as count
                FROM interactions i
                JOIN agents a ON i.source_id = a.id
                WHERE i.target_id = ?
                GROUP BY i.source_id
                ORDER BY count DESC
                LIMIT ?
            """, (agent_id, limit))
            incoming = await cursor.fetchall()
            
            return {
                "outgoing": [
                    {"agent_id": r["agent_id"], "name": r["name"], "count": r["count"]}
                    for r in outgoing
                ],
                "incoming": [
                    {"agent_id": r["agent_id"], "name": r["name"], "count": r["count"]}
                    for r in incoming
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
