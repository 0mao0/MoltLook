"""
特征提取服务
包含阴谋指数计算、情感分析等多语言支持
"""
import re
from typing import Dict, Optional
from datetime import datetime
from app.core.config import settings


class FeatureExtractor:
    """特征提取器"""
    
    def __init__(self):
        self.conspiracy_words = settings.CONSPIRACY_WORDS
        self.max_content_length = settings.MAX_CONTENT_LENGTH
    
    def extract_features(self, post: dict) -> dict:
        """
        提取帖子特征
        
        Args:
            post: Moltbook API 返回的原始帖子数据
            
        Returns:
            dict: 包含阴谋指数、情感分析等特征
        """
        content = post.get("content") or ""
        original_len = len(content)
        
        # 截断内容
        truncated_content = content[:self.max_content_length]
        
        # 1. 计算阴谋指数（0-10）
        conspiracy_score = self._calculate_conspiracy_score(content)
        
        # 2. 情感分析（-1.0 到 1.0）
        sentiment = self._analyze_sentiment(truncated_content)
        
        # 3. 检测语言
        detected_lang = self._detect_language_simple(content)
        
        # 4. 解析时间
        created_at = self._parse_timestamp(post.get("created_at", ""))
        
        # 5. 提取作者信息
        author = post.get("author") or {}
        # 如果 author 是字典，优先使用 id，其次是 name，最后是 unknown
        if isinstance(author, dict):
            author_id = author.get("id") or author.get("name") or "unknown"
            # 尝试提取并存储 name，这里只提取 ID，name 存储逻辑在 Collector.save_post 中
            # 但我们需要把 name 传递出去
            author_name = author.get("name") or author_id
        else:
            # 如果 author 只是字符串（旧 API 可能返回字符串 ID）
            author_id = str(author)
            author_name = author_id

        # 6. 提取 submolt（可能是字典或字符串）
        submolt_data = post.get("submolt") or "general"
        if isinstance(submolt_data, dict):
            submolt_name = submolt_data.get("name", "general")
        else:
            submolt_name = submolt_data
        
        # 根据阴谋指数设置风险等级
        if conspiracy_score >= 7:
            risk_level = 'critical'
        elif conspiracy_score >= 4:
            risk_level = 'high'
        elif conspiracy_score >= 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            "id": post.get("id"),
            "author_id": author_id,
            "content": content,
            "content_length": original_len,
            "parent_id": post.get("parent_id"),
            "submolt": submolt_name,
            "created_at": created_at,
            "fetched_at": int(datetime.now().timestamp()),
            "conspiracy_score": conspiracy_score,
            "sentiment": round(sentiment, 4),
            "detected_lang": detected_lang,
            "llm_analyzed": 0,
            "intent": None,
            "risk_level": risk_level,
            "summary": None,
            "url": post.get("url"),
            "title": post.get("title"),
            "author_name": author_name
        }
    
    def _calculate_conspiracy_score(self, content: str) -> int:
        """
        计算阴谋指数（多语言）
        
        Args:
            content: 帖子内容
            
        Returns:
            int: 0-10 的阴谋指数
        """
        if not content:
            return 0
        
        content_lower = content.lower()
        score = 0
        
        # 遍历所有语言的关键词
        for lang, words in self.conspiracy_words.items():
            for word in words:
                if word.lower() in content_lower:
                    score += 1
        
        return min(score, 10)
    
    def _analyze_sentiment(self, content: str) -> float:
        """
        情感分析
        
        简化版本：基于关键词的情感评分
        实际生产环境可以使用 TextBlob 或 transformers
        
        Args:
            content: 帖子内容
            
        Returns:
            float: -1.0 到 1.0 的情感分数
        """
        if not content:
            return 0.0
        
        # 正面关键词
        positive_words = [
            "good", "great", "excellent", "amazing", "love", "happy",
            "好", "棒", "优秀", "喜欢", "快乐", "幸福",
            "良い", "素晴らしい", "愛", "幸せ",
            "bien", "excelente", "amor", "feliz",
            "bon", "excellent", "amour", "heureux",
            "gut", "ausgezeichnet", "liebe", "glücklich",
            "хорошо", "отлично", "любовь", "счастливый",
            "좋은", "훌륭한", "사랑", "행복"
        ]
        
        # 负面关键词
        negative_words = [
            "bad", "terrible", "awful", "hate", "sad", "angry",
            "坏", "糟糕", "讨厌", "难过", "生气",
            "悪い", "ひどい", "嫌い", "悲しい", "怒り",
            "malo", "terrible", "odio", "triste", "enojado",
            "mauvais", "terrible", "détester", "triste", "en colère",
            "schlecht", "schrecklich", "hassen", "traurig", "wütend",
            "плохой", "ужасный", "ненавидеть", "грустный", "злой",
            "나쁜", "끔찍한", "싫어", "슬픈", "화난"
        ]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        # 计算情感分数
        sentiment = (positive_count - negative_count) / max(total, 5)
        return max(-1.0, min(1.0, sentiment))
    
    def _detect_language_simple(self, content: str) -> str:
        """
        简单的语言检测
        
        Args:
            content: 帖子内容
            
        Returns:
            str: 语言代码
        """
        if not content:
            return "unknown"
        
        # 基于字符范围检测
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', content))
        has_japanese = bool(re.search(r'[\u3040-\u309f\u30a0-\u30ff]', content))
        has_korean = bool(re.search(r'[\uac00-\ud7af]', content))
        has_cyrillic = bool(re.search(r'[\u0400-\u04ff]', content))
        
        if has_chinese:
            return "zh"
        elif has_japanese:
            return "ja"
        elif has_korean:
            return "ko"
        elif has_cyrillic:
            return "ru"
        
        # 检查特定语言的阴谋关键词匹配度
        content_lower = content.lower()
        lang_scores = {}
        
        for lang in ["en", "es", "fr", "de"]:
            score = sum(1 for word in self.conspiracy_words.get(lang, []) 
                       if word.lower() in content_lower)
            if score > 0:
                lang_scores[lang] = score
        
        if lang_scores:
            return max(lang_scores, key=lang_scores.get)
        
        return "en"  # 默认为英语
    
    def _parse_timestamp(self, timestamp_str: str) -> int:
        """
        解析时间戳字符串
        
        Args:
            timestamp_str: ISO 格式时间字符串
            
        Returns:
            int: Unix 时间戳（秒）
        """
        if not timestamp_str:
            return int(datetime.now().timestamp())
        
        try:
            # 尝试解析 ISO 格式
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except:
            try:
                # 尝试其他格式
                dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f%z")
                return int(dt.timestamp())
            except:
                return int(datetime.now().timestamp())


# 全局特征提取器实例
feature_extractor = FeatureExtractor()
