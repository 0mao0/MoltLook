"""
MoltLook FastAPI 主应用
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import db

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时初始化数据库
    logger.info("Initializing database...")
    await db.init_tables()
    logger.info("Database initialized successfully")
    
    yield
    
    # 关闭时清理资源
    logger.info("Shutting down...")
    await db.close()


# 创建 FastAPI 应用
app = FastAPI(
    title="MoltLook API",
    description="Moltbook 观测站后端 API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from app.api import dashboard, feed, network, agents, translation

# 注册路由
app.include_router(dashboard.router)
app.include_router(feed.router)
app.include_router(network.router)
app.include_router(agents.router)
app.include_router(translation.router)


@app.get("/")
async def root():
    """
    根路径 - API 信息
    """
    return {
        "name": "MoltLook API",
        "version": "1.0.0",
        "description": "Moltbook 观测站后端 API",
        "docs": "/docs",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "feed": "/api/feed",
            "network": "/api/network",
            "agents": "/api/agents"
        }
    }


@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": settings.DB_PATH.exists()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )
