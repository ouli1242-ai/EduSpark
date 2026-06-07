"""EduSpark 后端入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import get_settings
from app.core.database import init_db
from app.api import auth, profile, chat, resources, path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库"""
    settings = get_settings()
    Path(settings.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="EduSpark API",
    description="基于多智能体的个性化高等教育学习平台",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(resources.router)
app.include_router(path.router)

# 静态文件（本地存储的资源文件）
storage_path = Path(settings.LOCAL_STORAGE_PATH)
storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/api/files", StaticFiles(directory=str(storage_path)), name="files")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "EduSpark"}
