from pydantic import BaseModel, Field
from typing import Optional, List, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')

# 基础模型
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# 认证相关
class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1, description="密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# 相册相关
class AlbumBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="相册名称")
    description: Optional[str] = Field(None, max_length=500, description="相册描述")


class AlbumCreate(AlbumBase):
    pass


class AlbumUpdate(BaseModel):
    name: str = None
    description: str = None
    sort_order: int = None


class AlbumResponse(BaseModel):
    id: int
    name: str
    description: str = None
    cover_image: str = None
    sort_order: int = 0
    photo_count: int = 0
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# 照片相关
class PhotoBase(BaseModel):
    description: Optional[str] = Field(None, max_length=500, description="照片描述")


class PhotoResponse(BaseModel):
    id: int
    album_id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    width: int = None
    height: int = None
    description: Optional[str] = None
    sort_order: int = 0
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    url: str
    thumbnail_url: str
    created_at: datetime


# 相册详情（包含照片）
class AlbumDetailResponse(AlbumResponse):
    photos: List[PhotoResponse] = []


# 上传响应
class UploadResponse(BaseModel):
    message: str
    photo: PhotoResponse


# 通用响应
class MessageResponse(BaseModel):
    message: str


class PaginationResponse(BaseModel):
    page: int
    size: int
    total: int
    pages: int


class AlbumListResponse(BaseModel):
    albums: List[AlbumResponse]
    pagination: PaginationResponse


# 错误响应
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# 回收站响应
class TrashAlbumResponse(BaseModel):
    id: int
    name: str
    description: str = None
    cover_image: str = None
    photo_count: int = 0
    deleted_at: datetime
    created_at: datetime


class TrashPhotoResponse(BaseModel):
    id: int
    album_id: int
    album_name: str
    filename: str
    original_filename: str
    file_size: int
    description: Optional[str] = None
    deleted_at: datetime
    url: str
    thumbnail_url: str
    created_at: datetime


class TrashListResponse(BaseModel):
    albums: List[TrashAlbumResponse]
    photos: List[TrashPhotoResponse]
    total_albums: int
    total_photos: int


# 分页响应
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int