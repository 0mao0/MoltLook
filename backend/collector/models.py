"""
数据模型定义
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Agent:
    """社区成员"""
    id: str
    name: str
    description: str = ""
    karma: int = 0
    follower_count: int = 0
    following_count: int = 0
    is_claimed: bool = False
    is_active: bool = True
    created_at: Optional[str] = None
    last_active: Optional[str] = None
    influence_score: float = 0.0
    is_key_person: bool = False
    expertise_areas: List[str] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: dict) -> "Agent":
        """从API响应创建Agent对象"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "匿名"),
            description=data.get("description", ""),
            karma=data.get("karma", 0),
            follower_count=data.get("followerCount", 0),
            following_count=data.get("followingCount", 0),
            is_claimed=data.get("isClaimed", False),
            is_active=data.get("isActive", True),
            created_at=data.get("createdAt"),
            last_active=data.get("lastActive")
        )


@dataclass
class Post:
    """帖子"""
    id: str
    title: str
    content: str
    author_id: str
    author_name: str = ""
    submolt: str = ""
    score: int = 0
    upvotes: int = 0
    downvotes: int = 0
    comment_count: int = 0
    created_at: Optional[str] = None
    parent_id: Optional[str] = None
    is_reply: bool = False
    url: str = ""
    
    category: str = "other"
    summary: str = ""
    importance_score: float = 0.0
    engagement_score: float = 0.0
    is_top_news: bool = False
    keywords: List[str] = field(default_factory=list)
    
    conspiracy_score: int = 0
    sentiment: str = "neutral"
    risk_level: str = "low"
    
    @classmethod
    def from_api(cls, data: dict) -> "Post":
        """从API响应创建Post对象"""
        author = data.get("author", {})
        submolt = data.get("submolt", {})
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            content=data.get("content", ""),
            author_id=author.get("id", "") if isinstance(author, dict) else "",
            author_name=author.get("name", "匿名") if isinstance(author, dict) else str(author),
            submolt=submolt.get("name", "") if isinstance(submolt, dict) else str(submolt),
            score=data.get("score", 0),
            upvotes=data.get("upvotes", 0),
            downvotes=data.get("downvotes", 0),
            comment_count=data.get("comment_count", 0),
            created_at=data.get("created_at"),
            parent_id=data.get("parent_id"),
            is_reply=bool(data.get("parent_id")),
            url=data.get("url", "")
        )


@dataclass
class Interaction:
    """互动记录"""
    id: str
    from_agent_id: str
    to_agent_id: str
    post_id: str
    interaction_type: str
    created_at: Optional[str] = None
    
    @classmethod
    def from_reply(cls, post: Post) -> "Interaction":
        """从回复帖子创建互动记录"""
        return cls(
            id=f"int-{post.id}",
            from_agent_id=post.author_id,
            to_agent_id="",
            post_id=post.parent_id or "",
            interaction_type="reply",
            created_at=post.created_at
        )


@dataclass
class NewsItem:
    """新闻条目"""
    id: str
    post_id: str
    title: str
    summary: str
    category: str
    importance_score: float
    author_name: str
    created_at: str
    push_date: str = ""
    push_type: str = ""
    
    @classmethod
    def from_post(cls, post: Post, push_date: str, push_type: str) -> "NewsItem":
        """从帖子创建新闻条目"""
        return cls(
            id=f"news-{post.id}",
            post_id=post.id,
            title=post.title or "查看详情",
            summary=post.summary or post.content[:200] if post.content else "",
            category=post.category,
            importance_score=post.importance_score,
            author_name=post.author_name,
            created_at=post.created_at or "",
            push_date=push_date,
            push_type=push_type
        )


@dataclass
class PushRecord:
    """推送记录"""
    id: str
    push_type: str
    push_date: str
    news_count: int
    success: bool
    error_message: str = ""
    pushed_at: str = ""
    
    @classmethod
    def create(cls, push_type: str, push_date: str, news_count: int, success: bool, error: str = "") -> "PushRecord":
        """创建推送记录"""
        from datetime import datetime
        return cls(
            id=f"push-{push_type}-{push_date}",
            push_type=push_type,
            push_date=push_date,
            news_count=news_count,
            success=success,
            error_message=error,
            pushed_at=datetime.now().isoformat()
        )
