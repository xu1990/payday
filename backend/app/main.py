"""
薪日 PayDay 主服务入口 - 技术方案 2.1.1
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import async_session_maker
from app.api.v1 import api_router
from app.services.cache_preheat import preheat_all
from app.utils.logger import get_logger

logger = get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("Starting PayDay backend...")

    # 预热缓存
    try:
        async with async_session_maker() as db:
            results = await preheat_all(db)
            total = sum(results.values())
            logger.info(f"Cache preheated: {total} items")
    except Exception as e:
        logger.warning(f"Cache preheating failed: {e}")

    yield

    # 关闭时执行
    logger.info("Shutting down PayDay backend...")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(api_router)


@app.get("/")
def root():
    return {"app": settings.app_name}
