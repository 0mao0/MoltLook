"""
报告生成器
生成 Markdown 格式的日报和日志
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: Optional[str] = None):
        from core.config import settings
        self.output_dir = Path(output_dir or settings.LOGS_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.category_names = settings.NEWS_CATEGORY_NAMES
    
    def generate_daily_report(
        self,
        news_items: List[Dict[str, Any]],
        key_persons: List[Dict[str, Any]],
        stats: Dict[str, int],
        dangerous_posts: Optional[List[Dict[str, Any]]] = None,
        dangerous_agents: Optional[List[Dict[str, Any]]] = None,
        date: Optional[str] = None
    ) -> str:
        """
        生成每日报告
        
        Args:
            news_items: 新闻条目列表
            key_persons: 关键人物列表
            stats: 统计数据
            dangerous_posts: 危险言论列表
            dangerous_agents: 发布危险言论的成员列表
            date: 日期字符串
            
        Returns:
            str: Markdown 格式的报告
        """
        date_str = date or datetime.now().strftime("%Y-%m-%d")
        
        report = f"""# MoltLook 每日报告

**日期**: {date_str}

---

## 📊 数据统计

| 指标 | 数量 |
|------|------|
| 总帖子数 | {stats.get('total_posts', 0)} |
| 已分析帖子 | {stats.get('analyzed_posts', 0)} |
| 成员总数 | {stats.get('total_agents', 0)} |
| 关键人物 | {stats.get('key_persons', 0)} |
| Top 新闻 | {stats.get('top_news', 0)} |
| 互动记录 | {stats.get('interactions', 0)} |
| ⚠️ 危险言论 | {stats.get('dangerous_posts', 0)} |
| ⚠️ 危险用户 | {stats.get('dangerous_agents', 0)} |

---

## 📰 Top 新闻

"""
        
        news_by_category = {}
        for item in news_items:
            cat = item.get("category", "other")
            if cat not in news_by_category:
                news_by_category[cat] = []
            news_by_category[cat].append(item)
        
        for category in ["society", "technology", "economy", "speech", "other"]:
            items = news_by_category.get(category, [])
            if not items:
                continue
            
            cat_name = self.category_names.get(category, "其他")
            report += f"### {cat_name}\n\n"
            
            for i, item in enumerate(items[:10], 1):
                title = item.get("title") or "查看详情"
                summary = item.get("summary") or item.get("content", "")[:100] if item.get("content") else ""
                author = item.get("author_name") or "匿名"
                score = item.get("importance_score", 0)
                
                report += f"**{i}. {title}**\n"
                report += f"- 作者: {author}\n"
                report += f"- 重要性: {score:.1f}/10\n"
                if summary:
                    report += f"- 摘要: {summary}\n"
                report += "\n"
        
        report += """---

## 👥 关键人物

"""
        
        for i, person in enumerate(key_persons[:20], 1):
            name = person.get("name", "匿名")
            influence = person.get("influence_score", 0)
            karma = person.get("karma", 0)
            followers = person.get("follower_count", 0)
            expertise = person.get("expertise_areas", "[]")
            
            report += f"**{i}. {name}**\n"
            report += f"- 影响力: {influence:.1f}/10\n"
            report += f"- Karma: {karma}\n"
            report += f"- 关注者: {followers}\n"
            if expertise and expertise != "[]":
                report += f"- 专业领域: {expertise}\n"
            report += "\n"
        
        if dangerous_posts:
            report += """---

## ⚠️ 危险言论预警

"""
            
            for i, post in enumerate(dangerous_posts[:20], 1):
                title = post.get("title") or "无标题"
                author = post.get("author_name") or "匿名"
                danger_score = post.get("danger_score", 0)
                danger_type = post.get("danger_type", "未知")
                content = post.get("content", "")[:200] if post.get("content") else ""
                
                report += f"**{i}. {title}**\n"
                report += f"- 作者: {author}\n"
                report += f"- 危险等级: {danger_score}/10\n"
                report += f"- 危险类型: {danger_type}\n"
                if content:
                    report += f"- 内容摘要: {content}...\n"
                report += "\n"
        
        if dangerous_agents:
            report += """---

## ⚠️ 危险用户

"""
            
            for i, agent in enumerate(dangerous_agents[:10], 1):
                name = agent.get("name", "匿名")
                danger_count = agent.get("danger_post_count", 0)
                post_count = agent.get("post_count", 0)
                karma = agent.get("karma", 0)
                
                report += f"**{i}. {name}**\n"
                report += f"- 危险言论数: {danger_count}\n"
                report += f"- 总发帖数: {post_count}\n"
                report += f"- Karma: {karma}\n"
                report += "\n"
        
        report += f"""
---

*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        return report
    
    def save_report(self, content: str, filename: Optional[str] = None) -> str:
        """
        保存报告到文件
        
        Args:
            content: 报告内容
            filename: 文件名
            
        Returns:
            str: 文件路径
        """
        filename = filename or f"daily_report_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Report saved: {filepath}")
        return str(filepath)
    
    def generate_push_content(
        self,
        news_items: List[Dict[str, Any]],
        push_type: str,
        date: str,
        danger_count: int = 0
    ) -> str:
        """
        生成推送内容
        
        Args:
            news_items: 新闻条目列表
            push_type: 推送类型 (morning/evening)
            date: 日期
            danger_count: 危险言论数量
            
        Returns:
            str: Markdown 格式的推送内容
        """
        type_name = "早报" if push_type == "morning" else "晚报"
        
        content = f"## 📰 MoltLook {type_name} - {date}\n\n"
        
        if danger_count > 0:
            content += f"⚠️ **危险言论预警**: 检测到 {danger_count} 条高危言论\n\n"
        
        news_by_category = {}
        for item in news_items:
            cat = item.get("category", "other")
            if cat not in news_by_category:
                news_by_category[cat] = []
            news_by_category[cat].append(item)
        
        for category in ["society", "technology", "economy", "speech"]:
            items = news_by_category.get(category, [])
            if not items:
                continue
            
            cat_name = self.category_names.get(category, "其他")
            content += f"### {cat_name}\n"
            
            for item in items[:3]:
                title = item.get("title") or "查看详情"
                content += f"- **{title}**\n"
            
            content += "\n"
        
        from core.config import settings
        content += f"\n👉 [查看详情]({settings.FRONTEND_URL})"
        
        return content
    
    def append_log(self, message: str, log_type: str = "info") -> str:
        """
        追加日志
        
        Args:
            message: 日志消息
            log_type: 日志类型
            
        Returns:
            str: 日志文件路径
        """
        log_file = self.output_dir / f"moltlook_{datetime.now().strftime('%Y%m%d')}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{log_type.upper()}] {message}\n")
        
        return str(log_file)


report_generator = ReportGenerator()
