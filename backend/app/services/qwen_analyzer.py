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
        str: AI 分析结果（100字以内）
    """
    if not posts:
        return "该 Agent 暂无发言记录。"
    
    # 检查 API Key 是否配置
    if not settings.AI_API_KEY:
        return "AI 分析功能暂不可用：API Key 未配置。请在 .env 文件中配置 AI_API_KEY。"
    
    # 收集高风险帖子（阴谋指数 >= 3）
    risk_posts = [
        {
            "content": post.get("content", "")[:500],  # 限制每条内容长度
            "score": post.get("conspiracy_score", 0)
        }
        for post in posts
        if post.get("conspiracy_score", 0) >= 3
    ]
    
    # 如果没有高风险帖子，分析所有帖子
    if not risk_posts:
        risk_posts = [
            {
                "content": post.get("content", "")[:500],
                "score": post.get("conspiracy_score", 0)
            }
            for post in posts[:10]  # 最多分析10条
        ]
    
    # 构建分析提示
    posts_text = "\n".join([
        f"[阴谋指数 {p['score']}] {p['content'][:200]}..."
        for p in risk_posts[:5]  # 最多5条
    ])
    
    prompt = f"""请分析以下 Agent 的言论特征，判断其风险等级，并给出简明理由（100字以内）：

Agent 名称：{agent_name}
发言记录：
{posts_text}

请从以下维度分析：
1. 发言内容的主题和倾向
2. 是否包含阴谋论相关词汇
3. 是否有煽动性或极端言论
4. 综合风险评估

请用中文回答，控制在100字以内，条理清晰、有理有据。"""

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
                        "content": "你是一个专业的网络安全分析师，专注于分析社交媒体上的阴谋论言论。你的分析要客观、有理有据，语言简洁明了。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 300,
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
                    
                    # 截取前100字
                    if len(content) > 100:
                        content = content[:100]
                    
                    return content if content else "AI 分析失败，未能生成分析结果。"
                else:
                    error_text = await response.text()
                    return f"AI 分析失败（HTTP {response.status}）：{error_text[:50]}..."
    
    except aiohttp.ClientError as e:
        return f"AI 分析失败：网络错误 - {str(e)[:50]}"
    except Exception as e:
        return f"AI 分析失败：{str(e)[:50]}"
