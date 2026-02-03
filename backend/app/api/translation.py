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
        "fallback": fallback
    }


@router.post("/analyze")
async def analyze_post(
    content: str = Body(..., embed=True),
    risk_level: str = Body(..., embed=True),
    target_lang: str = Body("zh", embed=True)
):
    """
    分析帖子风险原因
    
    Args:
        content: 帖子内容
        risk_level: 当前风险等级
        target_lang: 目标语言
        
    Returns:
        分析结果
    """
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    if not settings.AI_API_KEY:
        return {
            "analysis": f"AI 分析未配置。该帖子被评为 {risk_level} 风险，可能是由于包含敏感词或异常交互模式。",
            "fallback": True
        }

    prompt = f"""你是一个 Molt 社区的安全分析专家。
当前帖子内容如下：
---
{content}
---
该帖子已被系统自动评定为“{risk_level}”风险等级。

请分析并解释为什么该帖子会被评定为这个风险等级。你的回答应该：
1. 直接给出分析原因，不需要开场白。
2. 重点分析内容中的敏感倾向、潜在威胁或异常意图。
3. 使用 {target_lang} 语言回答。
4. 语言要客观、专业。
5. 长度控制在 100 字以内。"""

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
        "max_tokens": 1000,
        "temperature": 0.5
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.AI_API_URL, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"AI API 错误: {error_text}")
                    return {
                        "analysis": f"分析失败 (API Error)。该帖子风险等级为: {risk_level}",
                        "fallback": True
                    }
                
                data = await response.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    analysis = data["choices"][0]["message"]["content"]
                    analysis = analysis.strip().strip('"').strip("'")
                    return {
                        "analysis": analysis,
                        "fallback": False
                    }
                return {
                    "analysis": f"分析失败 (No Content)。该帖子风险等级为: {risk_level}",
                    "fallback": True
                }
                    
    except Exception as e:
        logger.error(f"分析过程出错: {e}")
        return {
            "analysis": f"分析过程出错: {str(e)}。该帖子风险等级为: {risk_level}",
            "fallback": True
        }
