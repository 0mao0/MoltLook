"""
配置管理
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """系统配置"""
    
    PROJECT_NAME: str = "MoltLook"
    PROJECT_DESC: str = "MoltBook的彭博社 - 社区舆情分析系统"
    
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    DB_PATH: str = str(DATA_DIR / "moltlook.db")
    
    MOLTBOOK_API_KEY: str = ""
    MOLTBOOK_BASE_URL: str = "https://www.moltbook.com/api/v1"
    AGENT_NAME: str = ""
    
    AI_API_URL: str = ""
    AI_MODEL: str = "Qwen3-VL-30B-A3B-Instruct-FP8"
    AI_API_KEY: str = ""
    
    WECOM_WEBHOOK_URL: str = ""
    WECOM_ENABLED: bool = True
    
    FRONTEND_URL: str = "http://localhost:8045/"
    
    FETCH_INTERVAL: int = 300
    FETCH_SORT: str = "new"
    BATCH_SIZE: int = 100
    
    MORNING_PUSH_HOUR: int = 7
    EVENING_PUSH_HOUR: int = 17
    
    NEWS_CATEGORIES: List[str] = ["society", "technology", "economy", "speech", "other"]
    NEWS_CATEGORY_NAMES: dict = {
        "society": "社会",
        "technology": "技术",
        "economy": "经济",
        "speech": "言论",
        "other": "其他"
    }
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "moltlook.log"
    MD_REPORT_FILE: str = "daily_report.md"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
