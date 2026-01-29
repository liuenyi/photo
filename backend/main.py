from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os
from datetime import datetime

# 导入路由
from app.routers import auth, albums, photos, upload, admin
from app.database import init_db
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print(f"[启动] 小宇相册 API 服务启动中...")
    
    # 初始化数据库
    await init_db()
    
    # 创建上传目录
    os.makedirs("uploads", exist_ok=True)
    
    print(f"[地址] 服务地址: http://localhost:{settings.port}")
    print(f"[文档] API 文档: http://localhost:{settings.port}/docs")
    print(f"[管理] 管理后台: http://localhost:{settings.port}/admin/")
    print(f"[时间] 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    yield
    
    # 关闭时执行
    print("[关闭] 小宇相册 API 服务已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="小宇相册 API",
    description="一个现代化的相册管理 API 服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 注册 API 路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(albums.router, prefix="/api/albums", tags=["相册"])
app.include_router(photos.router, prefix="/api/photos", tags=["照片"])
app.include_router(upload.router, prefix="/api/upload", tags=["上传"])

# 注册管理后台路由
app.include_router(admin.router, prefix="/admin", tags=["管理后台"])


# 根路由
@app.get("/", tags=["系统"])
async def root():
    """
    API 服务信息
    """
    return {
        "message": "小宇相册 API 服务",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc",
        "admin": "/admin/"
    }


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    ) 