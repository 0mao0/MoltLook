"""
FastAPI 应用入口
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from storage.database import Database

logger = logging.getLogger(__name__)

db = Database()

app = FastAPI(
    title="MoltLook API",
    description="MoltLook 社区监控系统 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await db.init_tables()
    logger.info("API database initialized")


@app.on_event("shutdown")
async def shutdown():
    logger.info("API shutdown")


@app.get("/api/dashboard/stats")
async def get_dashboard_stats(days: int = 7):
    """获取仪表盘统计数据"""
    stats = await db.get_stats()
    return {"data": stats}


@app.get("/api/stats/realtime")
async def get_realtime_stats():
    """获取实时统计"""
    stats = await db.get_stats()
    return {"data": stats}


@app.get("/api/dashboard/risk-distribution")
async def get_risk_distribution():
    """获取风险分布"""
    return {"data": {}}


@app.get("/api/dashboard/network-graph")
async def get_network_graph():
    """获取网络图数据"""
    agents = await db.get_key_persons(limit=50)
    return {"data": {"nodes": agents, "edges": []}}


@app.get("/api/feed")
async def get_feed(
    page: int = 1,
    pageSize: int = 20,
    min_score: Optional[float] = None,
    submolt: Optional[str] = None,
    risk_level: Optional[str] = None
):
    """获取帖子列表"""
    if risk_level:
        danger_scores = {
            'low': (0, 3),
            'medium': (3, 5),
            'high': (5, 8),
            'critical': (8, 10)
        }
        score_range = danger_scores.get(risk_level)
        if score_range:
            posts = await db.get_dangerous_posts(
                min_score=score_range[0],
                max_score=score_range[1],
                limit=pageSize
            )
            return {"data": {"items": posts, "total": len(posts), "page": page}}
    
    posts = await db.get_top_news(limit=pageSize)
    return {"data": {"items": posts, "total": len(posts), "page": page}}


@app.get("/api/posts/{post_id}")
async def get_post(post_id: str):
    """获取帖子详情"""
    return {"data": None}


@app.get("/api/posts/{post_id}/comments")
async def get_post_comments(post_id: str):
    """获取帖子评论"""
    return {"data": []}


@app.get("/api/network")
async def get_network(limit: int = 100, community_id: Optional[int] = None):
    """获取网络数据"""
    agents = await db.get_key_persons(limit=limit)
    return {"data": {"nodes": agents, "edges": []}}


@app.get("/api/network/communities")
async def get_communities():
    """获取社区列表"""
    return {"data": []}


@app.get("/api/network/agent/{agent_id}/connections")
async def get_agent_connections(agent_id: str, limit: int = 20):
    """获取成员连接"""
    return {"data": []}


@app.get("/api/agents")
async def get_agents(
    page: int = 1,
    page_size: int = 20,
    risk_level: Optional[str] = None,
    community_id: Optional[int] = None
):
    """获取成员列表"""
    agents = await db.get_all_agents(limit=page_size, offset=(page - 1) * page_size)
    return {"data": {"items": agents, "total": len(agents), "page": page}}


@app.get("/api/agent/{agent_id}")
async def get_agent(agent_id: str):
    """获取成员详情"""
    return {"data": None}


@app.get("/api/agents/risky")
async def get_risky_agents(limit: int = 20, min_conspiracy: int = 0):
    """获取危险成员"""
    agents = await db.get_dangerous_agents(limit=limit)
    return {"data": agents}


@app.get("/api/agents/stats")
async def get_agents_stats():
    """获取成员统计"""
    stats = await db.get_stats()
    return {"data": stats}


@app.get("/api/agents/search")
async def search_agents(query: str, limit: int = 10):
    """搜索成员"""
    return {"data": []}


@app.get("/api/agent/{agent_id}/analyze")
async def analyze_agent(agent_id: str):
    """分析成员"""
    return {"data": None}


@app.post("/api/translate")
async def translate(content: str):
    """翻译"""
    return {"data": {"translated": content}}


@app.post("/api/analyze")
async def analyze(content: str, risk_level: str, target_lang: str):
    """分析"""
    return {"data": {}}


@app.get("/api/push-records")
async def get_push_records(
    date: Optional[str] = None,
    limit: int = 30
):
    """
    获取推送记录列表
    
    Args:
        date: 日期筛选
        limit: 数量限制
    """
    records = await db.get_push_records(limit=limit)
    return {"data": records}


@app.get("/api/push-records/{push_id}")
async def get_push_record(push_id: str):
    """
    获取单条推送记录详情
    
    Args:
        push_id: 推送记录ID (格式: YYYY-MM-DD-morning 或 YYYY-MM-DD-evening)
    """
    record = await db.get_push_record_by_id(push_id)
    if not record:
        return {"data": None}
    
    push_type = record.get("push_type")
    push_date = record.get("push_date")
    news_count = record.get("news_count", 10)
    
    if push_type == "morning":
        date = datetime.strptime(push_date, "%Y-%m-%d")
        start_time = date.replace(hour=17, minute=0, second=0)
        start_time = start_time - timedelta(days=1)
        end_time = date.replace(hour=7, minute=0, second=0)
    else:
        date = datetime.strptime(push_date, "%Y-%m-%d")
        start_time = date.replace(hour=7, minute=0, second=0)
        end_time = date.replace(hour=17, minute=0, second=0)
    
    start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    news_items = await db.get_top_news(
        limit=news_count,
        start_time=start_time_str,
        end_time=end_time_str
    )
    dangerous_posts = await db.get_dangerous_posts(
        limit=10,
        start_time=start_time_str,
        end_time=end_time_str
    )
    
    return {
        "data": {
            "record": record,
            "news": news_items,
            "dangerous_posts": dangerous_posts,
            "time_range": {
                "start": start_time_str,
                "end": end_time_str
            }
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
