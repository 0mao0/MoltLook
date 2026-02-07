"""
AI 分析服务
用于对Agent言论进行深度分析
"""
import aiohttp
import json
from typing import List, Dict, Optional
from app.core.config import settings


async def analyze_agent_risk(agent_name: str, posts: List[Dict]) -> str:
    """
    使用 AI 分析 Agent 的风险言论
    
    Args:
        agent_name: Agent 名称
        posts: 帖子列表，包含 content 和 conspiracy_score
    
    Returns:
        str: AI 分析结果
    """
    if not posts:
        return "该 Agent 暂无发言记录。"
    
    # 检查 API Key 是否配置
    if not settings.AI_API_KEY:
        return "AI 分析功能暂不可用：API Key 未配置。请在 .env 文件中配置 AI_API_KEY。"
    
    # 收集高风险帖子（阴谋指数 >= 3）
    risk_posts = [
        {
            "content": post.get("content", "")[:100],  # 限制每条内容长度 100 字符
            "score": post.get("conspiracy_score", 0)
        }
        for post in posts
        if post.get("conspiracy_score", 0) >= 3
    ]
    
    # 如果没有高风险帖子，分析所有帖子
    if not risk_posts:
        risk_posts = [
            {
                "content": post.get("content", "")[:100],
                "score": post.get("conspiracy_score", 0)
            }
            for post in posts[:5]
        ]
    
    # 构建分析提示
    posts_text = "\n".join([
        f"[阴谋指数 {p['score']}] {p['content']}"
        for p in risk_posts[:3]  # 最多3条
    ])

    prompt = f"""请简洁分析以下 Agent 的言论特征：

Agent 名称：{agent_name}
发言记录：
{posts_text}

请用 100 字以内回答，包含：
1. 主要主题和倾向
2. 是否包含阴谋论词汇
3. 简短风险评估"""

    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {settings.AI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": settings.AI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的网络安全分析师，专注于分析社交媒体上的阴谋论言论。你的分析要简洁有力，直击要点。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.3
            }
            
            async with session.post(
                settings.AI_API_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # 限制在150字以内（AI会自动根据max_tokens控制）
                    if len(content) > 150:
                        content = content[:150]
                    
                    return content if content else "AI 分析失败，未能生成分析结果。"
                else:
                    error_text = await response.text()
                    return f"AI 分析失败（HTTP {response.status}）：{error_text[:100]}..."
    
    except aiohttp.ClientError as e:
        return f"AI 分析失败：网络错误 - {str(e)[:100]}"
    except Exception as e:
        return f"AI 分析失败：{str(e)[:100]}"
