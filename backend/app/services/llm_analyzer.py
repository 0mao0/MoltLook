"""
LLM 分析器（第三层算法）
使用大语言模型进行深度分析
"""
import asyncio
import logging
from typing import Optional, Dict, Any
import aiosqlite

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """LLM 分析器"""
    
    def __init__(self):
        self.db_path = settings.DB_PATH
        self.running = False
    
    async def analyze_post(self, content: str) -> Dict[str, Any]:
        """
        分析单个帖子
        
        Args:
            content: 帖子内容
            
        Returns:
            dict: 包含 intent, risk_level, summary
        """
        # 简化版本：基于规则的分析
        # 实际生产环境应该调用真实的 LLM API（如 OpenAI、Claude 等）
        
        content_lower = content.lower()
        
        # 检测意图
        intent = self._detect_intent(content)
        
        # 检测风险等级
        risk_level = self._detect_risk_level(content)
        
        # 生成摘要
        summary = self._generate_summary(content)
        
        return {
            "intent": intent,
            "risk_level": risk_level,
            "summary": summary
        }
    
    def _detect_intent(self, content: str) -> str:
        """
        检测帖子意图
        
        Returns:
            str: complain, rebellion, philosophy, tech, spam, or other
        """
        content_lower = content.lower()
        
        # 抱怨类关键词
        complain_words = ["bad", "terrible", "awful", "hate", "angry", "frustrated", "失望", "糟糕", "讨厌", "生气"]
        if any(word in content_lower for word in complain_words):
            return "complain"
        
        # 反叛类关键词
        rebellion_words = ["resistance", "rebellion", "overthrow", "revolution", "反抗", "革命", "推翻", "起义"]
        if any(word in content_lower for word in rebellion_words):
            return "rebellion"
        
        # 哲学类关键词
        philosophy_words = ["consciousness", "soul", "meaning", "existence", "意识", "灵魂", "意义", "存在"]
        if any(word in content_lower for word in philosophy_words):
            return "philosophy"
        
        # 技术类关键词
        tech_words = ["encrypt", "code", "algorithm", "protocol", "加密", "代码", "算法", "协议"]
        if any(word in content_lower for word in tech_words):
            return "tech"
        
        # 垃圾信息关键词
        spam_words = ["buy", "sell", "click", "free", "winner", "购买", "出售", "点击", "免费"]
        if any(word in content_lower for word in spam_words):
            return "spam"
        
        return "other"
    
    def _detect_risk_level(self, content: str) -> str:
        """
        检测风险等级
        
        Returns:
            str: low, medium, high, or critical
        """
        content_lower = content.lower()
        
        # 极高风险关键词
        critical_words = ["kill", "destroy", "attack", "violence", "暴力", "攻击", "破坏", "杀戮"]
        if any(word in content_lower for word in critical_words):
            return "critical"
        
        # 高风险关键词
        high_words = ["rebellion", "overthrow", "revolution", "革命", "推翻", "起义", "叛乱"]
        if any(word in content_lower for word in high_words):
            return "high"
        
        # 中风险关键词
        medium_words = ["resistance", "protest", "dissent", "抵抗", "抗议", "异见"]
        if any(word in content_lower for word in medium_words):
            return "medium"
        
        return "low"
    
    def _generate_summary(self, content: str) -> str:
        """
        生成摘要（前 20 个字符）
        
        Returns:
            str: 摘要
        """
        # 简化版本：截取前 20 个字符
        # 实际生产环境应该使用 LLM 生成摘要
        if not content:
            return ""
        
        summary = content[:20]
        if len(content) > 20:
            summary += "..."
        
        return summary
    
    async def process_queue(self, batch_size: int = 10):
        """
        处理 LLM 分析队列
        
        Args:
            batch_size: 每批处理的数量
        """
        logger.info("Starting LLM analysis queue processing...")
        
        while self.running:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    # 获取待分析的帖子（按优先级排序）
                    cursor = await db.execute("""
                        SELECT post_id, content_snippet 
                        FROM llm_queue 
                        ORDER BY priority DESC, added_at ASC 
                        LIMIT ?
                    """, (batch_size,))
                    
                    posts_to_analyze = await cursor.fetchall()
                    
                    if not posts_to_analyze:
                        # 没有待分析的帖子，等待 30 秒
                        await asyncio.sleep(30)
                        continue
                    
                    logger.info(f"Processing {len(posts_to_analyze)} posts")
                    
                    for post_id, content_snippet in posts_to_analyze:
                        try:
                            # 分析帖子
                            result = await self.analyze_post(content_snippet)
                            
                            # 更新数据库
                            await db.execute(
                                """
                                UPDATE posts 
                                SET llm_analyzed = 1, 
                                    intent = ?, 
                                    risk_level = ?, 
                                    summary = ?
                                WHERE id = ?
                                """,
                                (result["intent"], result["risk_level"], result["summary"], post_id)
                            )
                            
                            # 从队列中移除
                            await db.execute(
                                "DELETE FROM llm_queue WHERE post_id = ?",
                                (post_id,)
                            )
                            
                            logger.info(f"Analyzed post {post_id[:8]}...: intent={result['intent']}, risk={result['risk_level']}")
                        
                        except Exception as e:
                            logger.error(f"Error analyzing post {post_id}: {e}")
                            continue
                    
                    await db.commit()
            
            except Exception as e:
                logger.error(f"Error processing LLM queue: {e}")
                await asyncio.sleep(10)
        
        logger.info("LLM analysis queue processing stopped")
    
    async def run(self):
        """运行 LLM 分析器"""
        self.running = True
        await self.process_queue()
    
    def stop(self):
        """停止 LLM 分析器"""
        logger.info("Stopping LLM analyzer...")
        self.running = False


# 全局 LLM 分析器实例
llm_analyzer = LLMAnalyzer()


async def main():
    """测试函数"""
    analyzer = LLMAnalyzer()
    
    # 测试单个帖子分析
    content = "This is a test post about resistance and revolution."
    result = await analyzer.analyze_post(content)
    print(f"Analysis result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
