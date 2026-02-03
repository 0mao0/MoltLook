"""
Pydantic 数据模型
用于请求/响应数据验证
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.core.config import settings


class PostBase(BaseModel):
    """帖子基础模型"""
    id: str
    author_id: str
    content: str = Field(..., max_length=settings.MAX_CONTENT_LENGTH)
    content_length: int
    parent_id: Optional[str] = None
    submolt: str = "general"
    created_at: int


class PostCreate(PostBase):
    """创建帖子模型"""
    conspiracy_score: int = Field(default=0, ge=0, le=10)
    sentiment: float = Field(default=0.0, ge=-1.0, le=1.0)


class PostResponse(PostBase):
    """帖子响应模型"""
    author_name: Optional[str] = None
    conspiracy_score: int
    sentiment: float
    risk_level: Optional[str] = None
    summary: Optional[str] = None
    llm_analyzed: int = 0
    intent: Optional[str] = None
    fetched_at: int
    url: Optional[str] = None
    title: Optional[str] = None
    
    class Config:
        from_attributes = True


class AgentBase(BaseModel):
    """Agent 基础模型"""
    id: str
    name: str
    description: Optional[str] = None


class AgentCreate(AgentBase):
    """创建 Agent 模型"""
    first_seen: int


class AgentResponse(AgentBase):
    """Agent 响应模型"""
    first_seen: int
    last_active: Optional[int] = None
    post_count: int = 0
    reply_count: int = 0
    be_replied_count: int = 0
    pagerank_score: float = 0.0
    community_id: int = -1
    risk_level: str = "low"
    avg_conspiracy_7d: float = 0.0
    
    class Config:
        from_attributes = True


class AgentProfile(AgentResponse):
    """Agent 详细档案"""
    recent_posts: List[PostResponse] = []
    connections: List[dict] = []


class InteractionBase(BaseModel):
    """互动基础模型"""
    source_id: str
    target_id: str
    post_id: str
    weight: float = 1.0
    created_at: int


class InteractionResponse(InteractionBase):
    """互动响应模型"""
    id: int
    
    class Config:
        from_attributes = True


class NetworkData(BaseModel):
    """网络图数据"""
    nodes: List[dict]
    edges: List[dict]


class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    total_posts: int
    active_agents: int
    avg_risk: float
    danger_count: int
    risk_level: str


class TrendData(BaseModel):
    """趋势数据"""
    date: str
    count: int


class DashboardResponse(BaseModel):
    """仪表盘响应"""
    stats: DashboardStats
    trend: List[TrendData]


class FeedQuery(BaseModel):
    """Feed 查询参数"""
    limit: int = Field(default=50, ge=1, le=100)
    min_score: int = Field(default=0, ge=0, le=10)
    submolt: Optional[str] = None


class LLMQueueItem(BaseModel):
    """LLM 队列项"""
    post_id: str
    content_snippet: str
    priority: int
    added_at: int


class MoltbookPost(BaseModel):
    """Moltbook API 帖子结构"""
    id: str
    author: dict
    content: str
    title: Optional[str] = None
    url: Optional[str] = None
    submolt: str = "general"
    parent_id: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    created_at: str
    
    class Config:
        extra = "allow"


class CollectionState(BaseModel):
    """采集状态"""
    last_seen_id: Optional[str] = None
    last_fetch_time: int = 0
    total_posts: int = 0
