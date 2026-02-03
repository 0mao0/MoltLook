"""
Feed API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import aiosqlite

from app.core.config import settings
from app.models.schemas import PostResponse

router = APIRouter(prefix="/api", tags=["feed"])


@router.get("/feed")
async def get_feed(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    min_score: int = Query(default=0, ge=0, le=10),
    submolt: Optional[str] = None,
    risk_level: Optional[str] = None
):
    """
    获取 Feed 流（分页）
    
    Args:
        page: 页码
        page_size: 每页数量
        min_score: 最小阴谋指数
        submolt: 社区分区筛选
        risk_level: 风险等级筛选
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 构建查询条件
            where_clauses = ["p.conspiracy_score >= ?"]
            params = [min_score]
            
            if submolt and submolt.strip():
                where_clauses.append("p.submolt = ?")
                params.append(submolt)
            
            if risk_level and risk_level.strip():
                where_clauses.append("p.risk_level = ?")
                params.append(risk_level)
            
            where_str = " AND ".join(where_clauses)
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM posts p WHERE {where_str}"
            cursor = await db.execute(count_query, params)
            total = (await cursor.fetchone())[0]
            
            # 获取分页数据
            query = f"""
                SELECT 
                    p.id, p.author_id, a.name as author_name, p.content, p.content_length,
                    p.parent_id, p.submolt, p.created_at, p.fetched_at,
                    p.conspiracy_score, p.sentiment, p.risk_level,
                    p.intent, p.summary, p.llm_analyzed, p.url, p.title
                FROM posts p
                LEFT JOIN agents a ON p.author_id = a.id
                WHERE {where_str}
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
            """
            query_params = params + [page_size, offset]
            
            cursor = await db.execute(query, query_params)
            rows = await cursor.fetchall()
            
            posts = []
            for row in rows:
                posts.append({
                    "id": row["id"],
                    "author_id": row["author_id"],
                    "author_name": row["author_name"],
                    "content": row["content"],
                    "content_length": row["content_length"],
                    "parent_id": row["parent_id"],
                    "submolt": row["submolt"],
                    "created_at": row["created_at"],
                    "fetched_at": row["fetched_at"],
                    "conspiracy_score": row["conspiracy_score"],
                    "sentiment": row["sentiment"],
                    "risk_level": row["risk_level"],
                    "summary": row["summary"],
                    "llm_analyzed": row["llm_analyzed"],
                    "intent": row["intent"],
                    "url": row["url"],
                    "title": row["title"]
                })
            
            return {
                "posts": posts,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    """
    获取单个帖子详情
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            cursor = await db.execute(
                """
                SELECT 
                    p.id, p.author_id, a.name as author_name, p.content, p.content_length,
                    p.parent_id, p.submolt, p.created_at, p.fetched_at,
                    p.conspiracy_score, p.sentiment, p.risk_level,
                    p.intent, p.summary, p.llm_analyzed, p.url, p.title
                FROM posts p
                LEFT JOIN agents a ON p.author_id = a.id
                WHERE p.id = ?
                """,
                (post_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Post not found")
            
            return PostResponse(
                id=row["id"],
                author_id=row["author_id"],
                author_name=row["author_name"],
                content=row["content"],
                content_length=row["content_length"],
                parent_id=row["parent_id"],
                submolt=row["submolt"],
                created_at=row["created_at"],
                fetched_at=row["fetched_at"],
                conspiracy_score=row["conspiracy_score"],
                sentiment=row["sentiment"],
                risk_level=row["risk_level"],
                summary=row["summary"],
                llm_analyzed=row["llm_analyzed"],
                intent=row["intent"],
                url=row["url"],
                title=row["title"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/posts/{post_id}/comments")
async def get_post_comments(
    post_id: str,
    limit: int = Query(default=20, ge=1, le=50)
):
    """
    获取帖子的评论
    """
    try:
        async with aiosqlite.connect(settings.DB_PATH, timeout=30) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA busy_timeout = 5000;")
            
            cursor = await db.execute(
                """
                SELECT 
                    p.id, p.author_id, p.content, p.content_length,
                    p.created_at, p.conspiracy_score, p.sentiment
                FROM posts p
                WHERE p.parent_id = ?
                ORDER BY p.created_at DESC
                LIMIT ?
                """,
                (post_id, limit)
            )
            rows = await cursor.fetchall()
            
            comments = [
                {
                    "id": row["id"],
                    "author_id": row["author_id"],
                    "content": row["content"],
                    "content_length": row["content_length"],
                    "created_at": row["created_at"],
                    "conspiracy_score": row["conspiracy_score"],
                    "sentiment": row["sentiment"]
                }
                for row in rows
            ]
            
            return {"comments": comments, "count": len(comments)}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
