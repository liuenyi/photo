import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from datetime import datetime
from .config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# 创建异步会话
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()


# 数据库模型
class Album(Base):
    """相册模型"""
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0)  # 自定义排序
    is_deleted = Column(Boolean, default=False)  # 软删除标记
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Photo(Base):
    """照片模型"""
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)  # 自定义排序
    is_deleted = Column(Boolean, default=False)  # 软删除标记
    deleted_at = Column(DateTime, nullable=True)  # 删除时间
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """用户模型（简化版）"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# 数据库依赖注入
async def get_db():
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        
    print("[数据库] 数据库初始化完成")
    
    # 创建示例数据
    await create_sample_data()


async def create_sample_data():
    """创建示例数据"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        
        # 检查是否已有数据
        result = await session.execute(select(Album))
        if result.first():
            return
            
        # 创建示例相册
        sample_albums = [
            {
                "name": "风景摄影",
                "description": "美丽的自然风光",
                "cover_image": "https://picsum.photos/400/300?random=1",
                "sort_order": 3
            },
            {
                "name": "人像写真", 
                "description": "精美的人像摄影作品",
                "cover_image": "https://picsum.photos/400/300?random=2",
                "sort_order": 2
            },
            {
                "name": "城市建筑",
                "description": "现代都市的建筑美学",
                "cover_image": "https://picsum.photos/400/300?random=3",
                "sort_order": 1
            }
        ]
        
        for album_data in sample_albums:
            album = Album(**album_data)
            session.add(album)
            
        await session.commit()
        print("[数据库] 示例数据创建完成")