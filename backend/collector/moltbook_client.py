"""
Moltbook API 客户端
负责从 Moltbook 获取数据
"""
import urllib.request
import urllib.error
import json
import logging
import ssl
from typing import List, Optional, Dict, Any
from .models import Post, Agent

logger = logging.getLogger(__name__)


class MoltbookClient:
    """Moltbook API 客户端"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        from core.config import settings
        self.api_key = api_key or settings.MOLTBOOK_API_KEY
        self.base_url = base_url or settings.MOLTBOOK_BASE_URL
        
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def _request(self, url: str, method: str = "GET", data: Optional[dict] = None, timeout: int = 60) -> Optional[Any]:
        """
        发送 HTTP 请求
        
        Args:
            url: 请求 URL
            method: 请求方法
            data: 请求数据
            timeout: 超时时间
            
        Returns:
            响应数据
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            
            if data:
                req.data = json.dumps(data).encode("utf-8")
            
            response = urllib.request.urlopen(req, timeout=timeout, context=self.ssl_context)
            
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
            return None
            
        except urllib.error.HTTPError as e:
            if e.code == 429:
                logger.warning("Rate limited by Moltbook API")
            else:
                logger.error(f"HTTP error {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            logger.error(f"URL error: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"Request error: {type(e).__name__}: {e}")
            return None
    
    def get_posts(
        self, 
        sort: str = "new", 
        limit: int = 100,
        after: Optional[str] = None,
        submolt: Optional[str] = None
    ) -> List[Post]:
        """
        获取帖子列表
        
        Args:
            sort: 排序方式 (hot, new, top, rising)
            limit: 返回数量上限
            after: 分页游标
            submolt: 社区分区
            
        Returns:
            List[Post]: 帖子列表
        """
        params = [f"sort={sort}", f"limit={limit}"]
        if after:
            params.append(f"after={after}")
        if submolt:
            params.append(f"submolt={submolt}")
        
        url = f"{self.base_url}/posts?{'&'.join(params)}"
        
        data = self._request(url)
        
        if not data:
            return []
        
        posts_data = []
        if isinstance(data, list):
            posts_data = data
        elif isinstance(data, dict):
            posts_data = data.get("posts", data.get("data", []))
        
        return [Post.from_api(p) for p in posts_data]
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取单个成员信息
        
        Args:
            agent_id: 成员ID
            
        Returns:
            Agent: 成员对象
        """
        url = f"{self.base_url}/agents/{agent_id}"
        data = self._request(url)
        
        if data:
            return Agent.from_api(data)
        return None
    
    def get_interactions(self, post_id: str) -> List[Dict[str, Any]]:
        """
        获取帖子的互动数据
        
        Args:
            post_id: 帖子ID
            
        Returns:
            List[dict]: 互动列表
        """
        url = f"{self.base_url}/posts/{post_id}/comments"
        data = self._request(url)
        
        if data:
            return data if isinstance(data, list) else []
        return []
