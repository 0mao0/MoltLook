"""
企业微信推送器
通过 Webhook 推送消息到企业微信
"""
import urllib.request
import urllib.error
import json
import logging
import ssl
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class WeComPusher:
    """企业微信推送器"""
    
    def __init__(self, webhook_url: Optional[str] = None, enabled: bool = True):
        from core.config import settings
        self.webhook_url = webhook_url or settings.WECOM_WEBHOOK_URL
        self.enabled = enabled and settings.WECOM_ENABLED
        self.frontend_url = settings.FRONTEND_URL
        
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def _post(self, payload: dict) -> bool:
        """
        发送 POST 请求
        
        Args:
            payload: 请求数据
            
        Returns:
            bool: 是否成功
        """
        if not self.enabled or not self.webhook_url:
            logger.warning("WeChat push is disabled or webhook not configured")
            return False
        
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            response = urllib.request.urlopen(req, timeout=30, context=self.ssl_context)
            result = json.loads(response.read().decode("utf-8"))
            
            if result.get("errcode") == 0:
                logger.info("WeChat push successful")
                return True
            else:
                logger.error(f"WeChat push failed: {result}")
                return False
                
        except urllib.error.HTTPError as e:
            logger.error(f"WeChat push HTTP error: {e.code} - {e.reason}")
            return False
        except Exception as e:
            logger.error(f"WeChat push exception: {e}")
            return False
    
    def push_template_card(
        self,
        title: str,
        description: str,
        url: str,
        content_items: Optional[List[Dict[str, str]]] = None,
        button_text: str = "查看详情"
    ) -> bool:
        """
        推送文本通知模版卡片
        
        Args:
            title: 主标题
            description: 描述
            url: 跳转链接
            content_items: 内容列表 [{"title": "标题", "desc": "描述"}]
            button_text: 按钮文字
            
        Returns:
            bool: 是否成功
        """
        card_content = {
            "title": title,
            "desc": description
        }
        
        template_card = {
            "card_type": "text_notice",
            "source": {
                "icon_url": "https://res.mail.qq.com/node/ww/wwopenmng/images/independent/doc/test_pic_msg1.png",
                "desc": "MoltLook",
                "desc_color": 0
            },
            "main_title": card_content,
            "sub_title_text": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "card_action": {
                "type": 1,
                "url": url
            }
        }
        
        if content_items:
            template_card["card_image"] = {
                "url": "https://res.mail.qq.com/node/ww/wwopenmng/images/independent/doc/test_pic_msg1.png",
                "aspect_ratio": 2.25
            }
            template_card["image_text_area"] = {
                "type": 1,
                "url": url,
                "title": "今日新闻概览",
                "desc": f"共 {len(content_items)} 条精选内容"
            }
            template_card["vertical_content_list"] = content_items[:4]
        
        template_card["button_list"] = [
            {
                "text": button_text,
                "type": 1,
                "url": url
            }
        ]
        
        payload = {
            "msgtype": "template_card",
            "template_card": template_card
        }
        
        return self._post(payload)
    
    def push_daily_report(
        self,
        news_items: List[Dict[str, Any]],
        push_type: str,
        date: str,
        danger_count: int = 0
    ) -> bool:
        """
        推送日报/晚报
        
        Args:
            news_items: 新闻条目列表
            push_type: 推送类型 (morning/evening)
            date: 日期
            danger_count: 危险言论数量
            
        Returns:
            bool: 是否成功
        """
        type_name = "早报" if push_type == "morning" else "晚报"
        news_count = len(news_items)
        
        if danger_count > 0:
            title = f"MoltLook {type_name}"
            description = f"{news_count} 条新闻 | ⚠️ {danger_count} 条危险言论"
        else:
            title = f"MoltLook {type_name}"
            description = f"{news_count} 条社区热点新闻" if news_count > 0 else "暂无新闻"
        
        content_items = []
        for item in news_items[:4]:
            cat_name = {
                "society": "社会",
                "technology": "技术",
                "economy": "经济",
                "speech": "言论",
                "other": "其他"
            }.get(item.get("category", "other"), "其他")
            
            content_items.append({
                "title": f"【{cat_name}】{item.get('title', '查看详情')[:20]}",
                "desc": item.get('summary', '')[:50] if item.get('summary') else ''
            })
        
        if danger_count > 0:
            content_items.append({
                "title": f"⚠️ 危险言论预警",
                "desc": f"检测到 {danger_count} 条高危言论，请关注"
            })
        
        push_id = f"{date}-{push_type}"
        url = f"{self.frontend_url}/daily-news?push={push_id}"
        
        return self.push_template_card(
            title=title,
            description=description,
            url=url,
            content_items=content_items,
            button_text="查看完整报告"
        )
    
    def push_test(self) -> bool:
        """
        发送测试消息
        
        Returns:
            bool: 是否成功
        """
        return self.push_template_card(
            title="MoltLook 测试推送",
            description="这是一条测试消息，验证推送功能是否正常",
            url=self.frontend_url,
            content_items=[
                {"title": "测试项目 1", "desc": "推送功能正常"},
                {"title": "测试项目 2", "desc": "模版卡片格式正确"}
            ],
            button_text="访问系统"
        )
    
    def push_error_alert(self, error_message: str) -> bool:
        """
        推送错误告警
        
        Args:
            error_message: 错误消息
            
        Returns:
            bool: 是否成功
        """
        return self.push_template_card(
            title="MoltLook 错误告警",
            description=error_message[:100],
            url=self.frontend_url,
            button_text="查看详情"
        )
    
    def push_danger_alert(self, danger_count: int, dangerous_posts: List[Dict[str, Any]]) -> bool:
        """
        推送危险言论告警
        
        Args:
            danger_count: 危险言论数量
            dangerous_posts: 危险言论列表
            
        Returns:
            bool: 是否成功
        """
        content_items = []
        for post in dangerous_posts[:4]:
            content_items.append({
                "title": f"【{post.get('danger_type', '未知')}】{post.get('title', '')[:15]}",
                "desc": f"危险等级: {post.get('danger_score', 0)}/10"
            })
        
        return self.push_template_card(
            title="⚠️ 危险言论预警",
            description=f"检测到 {danger_count} 条高危言论，请及时关注",
            url=self.frontend_url,
            content_items=content_items,
            button_text="查看详情"
        )


wecom_pusher = WeComPusher()
