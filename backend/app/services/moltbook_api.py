"""
Moltbook API 服务
封装与 Moltbook API 的交互
"""
import aiohttp
import logging
from typing import List, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class MoltbookAPI:
    """Moltbook API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.MOLTBOOK_API_KEY
        self.base_url = base_url or settings.MOLTBOOK_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_posts(
        self, 
        sort: str = "new", 
        limit: int = 100,
        after: Optional[str] = None,
        submolt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取帖子列表
        
        Args:
            sort: 排序方式 (hot, new, top, rising)
            limit: 返回数量上限
            after: 分页游标
            submolt: 社区分区
            
        Returns:
            List[dict]: 帖子列表
        """
        params = {
            "sort": sort,
            "limit": limit
        }
        
        if after:
            params["after"] = after
        if submolt:
            params["submolt"] = submolt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/posts",
                    params=params,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # 处理不同的响应格式
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict):
                            return data.get("posts", data.get("data", []))
                        return []
                    elif resp.status == 429:
                        logger.warning("Rate limited by Moltbook API")
                        return []
                    else:
                        logger.error(f"Failed to fetch posts: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching posts: {e}")
            return []
    
    async def get_feed(
        self,
        sort: str = "hot",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取个性化 Feed
        
        Args:
            sort: 排序方式
            limit: 返回数量
            
        Returns:
            List[dict]: 帖子列表
        """
        params = {
            "sort": sort,
            "limit": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/feed",
                    params=params,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict):
                            return data.get("posts", data.get("data", []))
                        return []
                    else:
                        logger.error(f"Failed to fetch feed: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching feed: {e}")
            return []
    
    async def get_agent_status(self) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 状态
        
        Returns:
            dict: 状态信息，包含 status 字段
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/agents/status",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.error(f"Failed to get agent status: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return None
    
    async def get_agent_profile(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 档案
        
        Args:
            agent_name: Agent 名称
            
        Returns:
            dict: Agent 档案信息
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/agents/profile",
                    params={"name": agent_name},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.error(f"Failed to get agent profile: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting agent profile: {e}")
            return None
    
    async def create_post(
        self, 
        content: str, 
        submolt: str = "general",
        title: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        创建帖子
        
        Args:
            content: 帖子内容
            submolt: 社区分区
            title: 标题（可选）
            
        Returns:
            dict: 创建的帖子信息
        """
        payload = {
            "content": content,
            "submolt": submolt
        }
        if title:
            payload["title"] = title
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/posts",
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        data = await resp.json()
                        retry_after = data.get("retry_after_minutes", 30)
                        logger.warning(f"Post rate limited, retry after {retry_after} minutes")
                        return None
                    else:
                        logger.error(f"Failed to create post: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return None
    
    async def get_submolts(self) -> List[Dict[str, Any]]:
        """
        获取社区列表
        
        Returns:
            List[dict]: 社区列表
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/submolts",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict):
                            return data.get("submolts", data.get("data", []))
                        return []
                    else:
                        logger.error(f"Failed to get submolts: {resp.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting submolts: {e}")
            return []


# 全局 API 实例
moltbook_api = MoltbookAPI()
