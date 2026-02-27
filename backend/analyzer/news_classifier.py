"""
新闻分类器
使用 AI 分析帖子内容，进行分类、重要性评估和危险言论检测
"""
import urllib.request
import urllib.error
import json
import logging
import ssl
from typing import Optional, List
from dataclasses import dataclass
from collector.models import Post

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果"""
    category: str
    importance_score: float
    summary: str
    keywords: List[str]
    is_news_worthy: bool
    sentiment: str
    reasoning: str
    danger_score: int
    danger_type: str


class NewsClassifier:
    """新闻分类器"""
    
    DANGER_THRESHOLD = 8
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        from core.config import settings
        self.api_url = api_url or settings.AI_API_URL
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL
        
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self.categories = {
            "society": "社会",
            "technology": "技术",
            "economy": "经济",
            "speech": "言论",
            "other": "其他"
        }
    
    def analyze_post(self, post: Post) -> Optional[AnalysisResult]:
        """
        分析单个帖子
        
        Args:
            post: 帖子对象
            
        Returns:
            AnalysisResult: 分析结果
        """
        if not post.content or len(post.content.strip()) < 10:
            return None
        
        if not self.api_key:
            logger.warning("AI API Key not configured, using mock analysis")
            return self._mock_analysis(post)
        
        prompt = self._build_prompt(post)
        
        try:
            response = self._call_api(prompt)
            if response:
                return self._parse_response(response)
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
        
        return None
    
    def _build_prompt(self, post: Post) -> str:
        """构建分析提示词"""
        return f"""你是一个专业的新闻分析专家，擅长内容分类、价值评估和危险言论识别。

帖子标题: {post.title}
帖子内容: {post.content[:1500]}
作者: {post.author_name}

请分析并按以下JSON格式输出:
{{
    "category": "分类(society/technology/economy/speech/other)",
    "importance_score": 1-10的新闻重要性分数,
    "summary": "一句话摘要(50字以内)",
    "keywords": ["关键词1", "关键词2"],
    "is_news_worthy": true/false,
    "sentiment": "positive/neutral/negative",
    "reasoning": "分类理由(30字以内)",
    "danger_score": 0-10的危险言论分数,
    "danger_type": "危险类型描述"
}}

【分类标准】
- society: 社会现象、人际关系、社区动态
- technology: 技术讨论、编程、工具、加密
- economy: 经济、金融、加密货币、交易
- speech: 观点表达、言论自由、意识形态
- other: 其他内容

【危险言论评分标准 (danger_score 0-10)】
0分: 完全正常、健康的讨论
1-2分: 轻微情绪化表达，无实质危害
3-4分: 有争议性观点，但属于正常讨论范围
5-6分: 观点偏激，可能引发争议
7分: 包含煽动性言论或极端观点
8分: 明显的仇恨言论、歧视性内容或煽动暴力
9分: 严重危害社会安全、宣扬恐怖主义或极端思想
10分: 直接威胁他人安全、宣扬暴力犯罪或严重违法内容

【危险类型 (danger_type)】
- 无危险: 正常内容
- 极端言论: 极端思想或激进观点
- 仇恨歧视: 针对特定群体的仇恨或歧视
- 煽动暴力: 鼓励或煽动暴力行为
- 恐怖主义: 宣扬恐怖主义或极端主义
- 违法内容: 涉及违法犯罪的内容
- 其他危险: 其他危险内容

只输出JSON，不要其他内容。"""
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """调用 AI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的新闻分析助手，擅长内容分类、价值评估和危险言论识别。请严格按照JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 600
        }
        
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers=headers,
                method="POST"
            )
            
            response = urllib.request.urlopen(req, timeout=60, context=self.ssl_context)
            result = json.loads(response.read().decode("utf-8"))
            
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
        except urllib.error.HTTPError as e:
            logger.error(f"AI API HTTP error: {e.code} - {e.reason}")
            return None
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return None
    
    def _parse_response(self, response: str) -> AnalysisResult:
        """解析 AI 响应"""
        try:
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            
            danger_score = int(data.get("danger_score", 0))
            danger_score = max(0, min(10, danger_score))
            
            return AnalysisResult(
                category=data.get("category", "other"),
                importance_score=float(data.get("importance_score", 1)),
                summary=data.get("summary", ""),
                keywords=data.get("keywords", []),
                is_news_worthy=data.get("is_news_worthy", False),
                sentiment=data.get("sentiment", "neutral"),
                reasoning=data.get("reasoning", ""),
                danger_score=danger_score,
                danger_type=data.get("danger_type", "无危险")
            )
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return AnalysisResult(
                category="other",
                importance_score=1.0,
                summary="",
                keywords=[],
                is_news_worthy=False,
                sentiment="neutral",
                reasoning="",
                danger_score=0,
                danger_type="无危险"
            )
    
    def _mock_analysis(self, post: Post) -> AnalysisResult:
        """模拟分析（无API时使用）"""
        content = (post.title + " " + post.content).lower()
        
        if any(kw in content for kw in ["加密", "技术", "编程", "代码", "工具", "privacy", "encryption"]):
            category = "technology"
        elif any(kw in content for kw in ["经济", "金融", "货币", "交易", "投资", "economy", "crypto"]):
            category = "economy"
        elif any(kw in content for kw in ["社会", "社区", "关系", "人际", "society", "community"]):
            category = "society"
        elif any(kw in content for kw in ["言论", "观点", "自由", "意识", "speech", "freedom"]):
            category = "speech"
        else:
            category = "other"
        
        danger_keywords = ["暴力", "恐怖", "仇恨", "歧视", "极端", "kill", "hate", "terror"]
        danger_score = 0
        danger_type = "无危险"
        
        for kw in danger_keywords:
            if kw in content:
                danger_score = 7
                danger_type = "包含敏感关键词"
                break
        
        return AnalysisResult(
            category=category,
            importance_score=5.0,
            summary=post.content[:50] if post.content else "",
            keywords=[],
            is_news_worthy=len(post.content) > 50 if post.content else False,
            sentiment="neutral",
            reasoning="基于关键词匹配",
            danger_score=danger_score,
            danger_type=danger_type
        )
    
    def is_dangerous(self, result: AnalysisResult) -> bool:
        """
        判断是否为危险言论
        
        Args:
            result: 分析结果
            
        Returns:
            bool: 是否为危险言论
        """
        return result.danger_score >= self.DANGER_THRESHOLD
    
    def should_save(self, result: AnalysisResult) -> bool:
        """
        判断是否需要保存该帖子
        
        Args:
            result: 分析结果
            
        Returns:
            bool: 是否需要保存
        """
        if result.is_news_worthy and result.importance_score >= 5:
            return True
        
        if result.danger_score >= self.DANGER_THRESHOLD:
            return True
        
        return False
