"""EduSpark 后端入口"""
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import init_db
from app.api import auth, profile, chat, resources, path, evaluation, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库"""
    settings = get_settings()
    Path(settings.LOCAL_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
    init_db()
    print(f"[OK] 数据库表已初始化")
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
app.include_router(evaluation.router)
app.include_router(upload.router)

# 静态文件（本地存储的资源文件）
storage_path = Path(settings.LOCAL_STORAGE_PATH)
storage_path.mkdir(parents=True, exist_ok=True)
app.mount("/api/files", StaticFiles(directory=str(storage_path)), name="files")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "EduSpark"}


# 允许直接 python -m app.main 启动
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("  EduSpark 后端服务")
    print("  API 文档: http://localhost:8000/docs")
    print("  健康检查: http://localhost:8000/api/health")
    print("=" * 50)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
