"""
翻译 API 路由
使用 AI 接口翻译帖子内容
"""
import logging
from fastapi import APIRouter, HTTPException, Body
import aiohttp

from app.core.config import settings

router = APIRouter(prefix="/api", tags=["translation"])

logger = logging.getLogger(__name__)


async def translate_with_ai(content: str, source_lang: str = "en", target_lang: str = "zh") -> tuple[str, bool]:
    """
    使用 AI 接口翻译文本
    
    Args:
        content: 要翻译的内容
        source_lang: 源语言
        target_lang: 目标语言
        
    Returns:
        翻译后的文本
    """
    if not content or not content.strip():
        return ""
    
    if not settings.AI_API_KEY:
        logger.warning("AI API 密钥未配置，返回原文")
        return content, True
    
    prompt = f"""请将以下文本从{source_lang}翻译成{target_lang}，只返回翻译结果，不需要任何解释或格式：

{content}"""

    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": settings.AI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.3
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.AI_API_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"AI API 错误: {error_text}")
                    raise HTTPException(status_code=500, detail=f"AI API 错误: {error_text}")
                
                data = await response.json()
                
                if data.get("choices") and len(data["choices"]) > 0:
                    translation = data["choices"][0]["message"]["content"]
                    translation = translation.strip().strip('"').strip("'")
                    return translation, False
                return content, True
                    
    except aiohttp.ClientError as e:
        logger.error(f"AI API 请求失败: {e}")
        return content, True
    except Exception as e:
        logger.error(f"翻译过程出错: {e}")
        return content, True


@router.post("/translate")
async def translate_post(content: str = Body(..., embed=True)):
    """
    翻译帖子内容
    
    Args:
        content: 要翻译的帖子内容
        
    Returns:
        翻译结果
    """
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    if len(content) > 10000:
        raise HTTPException(status_code=400, detail="内容过长，最大支持10000字符")
    
    translation, fallback = await translate_with_ai(content)
    return {
        "original": content,
        "translation": translation,
        "source_lang": "en",
        "target_lang": "zh",
        "fallback": fallback
    }
