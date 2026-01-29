from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from typing import List
import os

from ..database import get_db, Photo, Album
from ..schemas import PhotoResponse, MessageResponse
from ..config import settings
from ..dependencies import get_current_user

router = APIRouter()


def photo_to_response(photo: Photo) -> PhotoResponse:
    """将Photo模型转换为PhotoResponse"""
    # 构建图片URL
    base_url = f"https://photo.liuenyi.com"
    
    # 原图URL
    url = f"{base_url}/uploads/{photo.filename}"
    
    # 缩略图URL
    thumbnail_url = f"{base_url}/uploads/thumb_{photo.filename}"
    
    # 如果是大文件（>10MB），检查是否有预览图
    preview_url = url  # 默认使用原图
    if photo.file_size and photo.file_size > 10 * 1024 * 1024:
        preview_path = os.path.join(settings.upload_dir, f"preview_{photo.filename}")
        if os.path.exists(preview_path):
            preview_url = f"{base_url}/uploads/preview_{photo.filename}"
    
    return PhotoResponse(
        id=photo.id,
        album_id=photo.album_id,
        filename=photo.filename,
        original_filename=photo.original_filename,
        file_path=photo.file_path,
        file_size=photo.file_size,
        width=photo.width,
        height=photo.height,
        description=photo.description,
        sort_order=photo.sort_order,
        url=preview_url,  # 使用预览图或原图
        thumbnail_url=thumbnail_url,
        created_at=photo.created_at
    )


@router.get("/album/{album_id}", summary="获取相册中的照片")
async def get_photos_by_album(
    album_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取指定相册中的照片列表
    
    - **album_id**: 相册ID
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大1000
    """
    # 检查相册是否存在
    album_result = await db.execute(
        select(Album).where(Album.id == album_id)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="相册不存在"
        )
    
    # 计算总数
    total_result = await db.execute(
        select(func.count(Photo.id)).where(Photo.album_id == album_id)
    )
    total = total_result.scalar() or 0
    
    # 计算偏移量
    offset = (page - 1) * size
    
    # 获取照片列表
    photos_result = await db.execute(
        select(Photo)
        .where(Photo.album_id == album_id)
        .order_by(Photo.sort_order.desc(), Photo.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    photos = photos_result.scalars().all()
    
    return {
        "items": [photo_to_response(photo) for photo in photos],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }


@router.get("/{photo_id}", response_model=PhotoResponse, summary="获取照片详情")
async def get_photo_detail(
    photo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    获取照片详情
    
    - **photo_id**: 照片ID
    """
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="照片不存在"
        )
    
    return photo_to_response(photo)


@router.put("/{photo_id}", response_model=PhotoResponse, summary="更新照片信息")
async def update_photo(
    photo_id: int,
    description: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    更新照片描述
    
    - **photo_id**: 照片ID
    - **description**: 照片描述
    """
    # 检查照片是否存在
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="照片不存在"
        )
    
    # 更新描述
    if description is not None:
        await db.execute(
            update(Photo)
            .where(Photo.id == photo_id)
            .values(description=description)
        )
        await db.commit()
        await db.refresh(photo)
    
    return photo_to_response(photo)


@router.put("/{photo_id}/sort", response_model=PhotoResponse, summary="更新照片排序")
async def update_photo_sort(
    photo_id: int,
    sort_order: int,
    db: AsyncSession = Depends(get_db)
):
    """更新照片排序"""
    result = await db.execute(select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    photo.sort_order = sort_order
    await db.commit()
    await db.refresh(photo)
    
    return photo_to_response(photo)


@router.delete("/{photo_id}", response_model=MessageResponse, summary="删除照片")
async def delete_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    删除照片
    
    - **photo_id**: 照片ID
    """
    # 检查照片是否存在
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="照片不存在"
        )
    
    # 删除文件 (TODO: 实际删除文件系统中的文件)
    
    # 删除数据库记录
    await db.execute(delete(Photo).where(Photo.id == photo_id))
    await db.commit()
    
    return MessageResponse(message="照片已删除")


@router.get("/", summary="获取照片列表")
async def get_photos(
    album_id: int = Query(None, description="相册ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=1000, description="每页数量"),
    sort_by: str = Query("default", description="排序方式: default, created_at, original_filename, file_size"),
    order: str = Query("desc", description="排序顺序: asc, desc"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取照片列表
    默认排序优先级：自定义排序 → 时间倒序 → 用户选择排序
    """
    # 构建查询条件
    query = select(Photo)
    count_query = select(func.count(Photo.id))
    
    if album_id:
        query = query.where(Photo.album_id == album_id)
        count_query = count_query.where(Photo.album_id == album_id)
    
    # 计算总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 构建排序条件
    if sort_by == "default":
        # 默认排序：先按自定义排序，再按创建时间倒序
        order_by = [Photo.sort_order.desc(), Photo.created_at.desc()]
    else:
        # 用户选择的排序
        sort_column = getattr(Photo, sort_by, Photo.created_at)
        if order == "desc":
            order_by = [sort_column.desc()]
        else:
            order_by = [sort_column.asc()]
    
    # 计算偏移量
    offset = (page - 1) * size
    
    # 执行查询
    result = await db.execute(
        query.order_by(*order_by).offset(offset).limit(size)
    )
    photos = result.scalars().all()
    
    return {
        "items": [photo_to_response(photo) for photo in photos],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }
