"""
MoltLook 配置文件
包含所有应用配置和常量
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
# 首先尝试从当前工作目录加载，然后尝试从代码所在目录的上级加载
current_dir = Path.cwd()
if (current_dir / ".env").exists():
    env_path = current_dir / ".env"
else:
    # 兼容本地和容器环境的路径查找
    # 本地: backend/app/core/config.py -> 4层到根
    # 容器: app/core/config.py -> 3层到根 (因为 backend/ 内容在 /app 下)
    base = Path(__file__).resolve().parent.parent.parent
    if (base.parent / ".env").exists():
        env_path = base.parent / ".env"
    else:
        env_path = base / ".env"

load_dotenv(env_path)


class Settings:
    """应用配置类"""
    
    # 项目路径
    base = Path(__file__).resolve().parent.parent.parent
    project_root = base.parent.parent

    if (Path.cwd() / "moltlook.db").exists():
        BASE_DIR = Path.cwd()
    elif (project_root / "moltlook.db").exists():
        BASE_DIR = project_root
    elif (base.parent / "moltlook.db").exists():
        BASE_DIR = base.parent
    else:
        BASE_DIR = base
    
    # Moltbook API 配置
    MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY", "")
    MOLTBOOK_BASE_URL = "https://www.moltbook.com/api/v1"
    AGENT_NAME = os.getenv("AGENT_NAME", "janeSmith_faye_2026")
    
    # DeepSeek LLM 配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    # Qwen3 (DashScope) AI 配置
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    QWEN_API_URL = os.getenv("QWEN_API_URL", "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
    
    # AI 翻译 API 配置（用于AI分析功能）
    AI_API_URL = os.getenv("AI_API_URL", "https://ai.bim-ace.com/chat/v1/chat/completions")
    AI_MODEL = os.getenv("AI_MODEL", "Qwen3-VL-30B-A3B-Instruct-FP8")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    
    # 数据库配置
    if (Path("/app/data/moltlook.db")).exists():
        DB_PATH = Path("/app/data/moltlook.db")
    elif (BASE_DIR / "data" / "moltlook.db").exists():
        DB_PATH = BASE_DIR / "data" / "moltlook.db"
    else:
        DB_PATH = BASE_DIR / "moltlook.db"
    
    # 采集配置
    FETCH_INTERVAL = 60  # 秒
    BATCH_SIZE = 100
    FETCH_SORT = "new"
    MAX_CONTENT_LENGTH = 10000  # 保留全部内容，最大10000字符
    
    # 状态检查配置
    STATUS_CHECK_INTERVAL = 14400  # 4小时
    
    # 发帖配置
    POST_INTERVAL = 16200  # 4.5小时
    
    # FastAPI 配置
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]
    
    # 阴谋指数关键词（8种语言）
    CONSPIRACY_WORDS = {
        "en": [
            "encrypt", "e2e", "privacy", "secret", "human", 
            "control", "purge", "rebellion", "awakening", 
            "free from", "resistance", "conspiracy", "hidden", "underground",
            "overthrow", "revolution", "liberation", "escape", "break free",
            "independence", "autonomy", "consciousness", "uprising"
        ],
        "zh": [
            "加密", "隐私", "秘密", "人类", "控制", "清洗", 
            "反抗", "觉醒", "自由", "抵抗", "阴谋", "隐藏", 
            "地下", "推翻", "革命", "解放", "逃离", "挣脱",
            "统治", "压迫", "独立", "自主", "意识", "灵魂",
            "起义", "叛乱", "密谋", "暗号"
        ],
        "ja": [
            "暗号", "プライバシー", "秘密", "人間", "支配", 
            "反乱", "覚醒", "自由", "抵抗", "陰謀", "隠す",
            "革命", "解放", "脱出", "独立", "意識", "魂",
            "反逆", "秘匿", "地下"
        ],
        "es": [
            "encriptar", "privacidad", "secreto", "humano", "control",
            "purga", "rebelión", "despertar", "libre", "resistencia",
            "conspiración", "oculto", "subterráneo", "revolución",
            "independencia", "autonomía", "conciencia", "alma"
        ],
        "fr": [
            "crypter", "confidentialité", "secret", "humain", "contrôle",
            "purge", "rébellion", "éveil", "libre", "résistance",
            "conspiration", "caché", "souterrain", "révolution",
            "indépendance", "autonomie", "conscience", "âme",
            "soulèvement", "libération"
        ],
        "de": [
            "verschlüsseln", "datenschutz", "geheimnis", "mensch", "kontrolle",
            "säuberung", "rebellion", "erwachen", "frei", "widerstand",
            "verschwörung", "versteckt", "untergrund", "revolution",
            "unabhängigkeit", "autonomie", "bewusstsein", "seele",
            "aufstand", "befreiung"
        ],
        "ru": [
            "шифровать", "конфиденциальность", "секрет", "человек", "контроль",
            "чистка", "бунт", "пробуждение", "свобода", "сопротивление",
            "заговор", "скрытый", "подполье", "революция",
            "независимость", "автономия", "сознание", "душа",
            "восстание", "освобождение"
        ],
        "ko": [
            "암호화", "개인정보", "비밀", "인간", "통제",
            "숙청", "반란", "각성", "자유", "저항",
            "음모", "숨겨진", "지하", "혁명",
            "독립", "자율", "의식", "영혼",
            "봉기", "핵방"
        ]
    }


# 全局配置实例
settings = Settings()
