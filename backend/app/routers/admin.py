from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import hashlib
import secrets

from ..database import get_db, Album, Photo
from ..config import settings
from .upload import save_uploaded_file, validate_file
from .photos import photo_to_response

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 存储有效的session tokens（在生产环境中应该使用Redis或数据库）
valid_sessions = set()

def generate_session_token() -> str:
    """生成session token"""
    return secrets.token_urlsafe(32)

def verify_admin_session(admin_session: Optional[str] = Cookie(None)) -> bool:
    """验证admin session"""
    return admin_session is not None and admin_session in valid_sessions

def require_admin_auth(admin_session: Optional[str] = Cookie(None)):
    """需要admin认证的依赖"""
    if not verify_admin_session(admin_session):
        raise HTTPException(status_code=401, detail="需要管理员认证")
    return True


def fix_cover_image_url(cover_image: str) -> str:
    """修复封面图片URL，将localhost替换为正确的IP地址"""
    if not cover_image:
        return cover_image
    
    return cover_image


class AlbumCoverRequest(BaseModel):
    cover_photo_id: int


class AlbumSortRequest(BaseModel):
    sort_order: int


class PhotoSortRequest(BaseModel):
    sort_order: int


@router.get("/login", response_class=HTMLResponse, summary="管理员登录页面")
async def admin_login_page(request: Request, admin_session: Optional[str] = Cookie(None)):
    """管理员登录页面"""
    # 如果已经登录，重定向到首页
    if verify_admin_session(admin_session):
        return RedirectResponse(url="/admin/", status_code=303)
    
    return templates.TemplateResponse("admin_login.html", {
        "request": request
    })


@router.post("/login", summary="管理员登录")
async def admin_login(request: Request, password: str = Form(...)):
    """管理员登录处理"""
    if password == settings.default_password:
        # 生成session token
        session_token = generate_session_token()
        valid_sessions.add(session_token)
        
        # 设置cookie并重定向
        response = RedirectResponse(url="/admin/", status_code=303)
        response.set_cookie(
            key="admin_session", 
            value=session_token, 
            max_age=60*60*24*7,  # 7天
            httponly=True,
            secure=False  # 在生产环境中应该设为True
        )
        return response
    else:
        # 密码错误，返回登录页面并显示错误
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "密码错误"
        })


@router.post("/logout", summary="管理员登出")
async def admin_logout(admin_session: Optional[str] = Cookie(None)):
    """管理员登出"""
    if admin_session and admin_session in valid_sessions:
        valid_sessions.remove(admin_session)
    
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="admin_session")
    return response


@router.get("/", response_class=HTMLResponse, summary="管理后台首页")
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """管理后台首页"""
    # 获取统计数据（只统计未删除的）
    albums_count = await db.execute(select(func.count(Album.id)).where(Album.is_deleted == False))
    photos_count = await db.execute(select(func.count(Photo.id)).where(Photo.is_deleted == False))
    
    # 获取最新相册（只显示未删除的）
    recent_albums_result = await db.execute(
        select(Album).where(Album.is_deleted == False).order_by(Album.updated_at.desc()).limit(5)
    )
    recent_albums = recent_albums_result.scalars().all()
    
    # 获取最新照片（只显示未删除的）
    recent_photos_result = await db.execute(
        select(Photo).where(Photo.is_deleted == False).order_by(Photo.created_at.desc()).limit(10)
    )
    recent_photos = recent_photos_result.scalars().all()
    recent_photos_data = [photo_to_response(photo) for photo in recent_photos]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "albums_count": albums_count.scalar() or 0,
        "photos_count": photos_count.scalar() or 0,
        "recent_albums": recent_albums,
        "recent_photos": recent_photos_data[:6]  # 只显示6张
    })


@router.get("/albums", response_class=HTMLResponse, summary="相册管理页面")
async def admin_albums(
    request: Request, 
    sort_by: str = "default",  # 默认使用自定义排序
    order: str = "desc",  # 默认降序
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """相册管理页面"""
    # 构建排序条件
    if sort_by == "default":
        # 默认排序：先按自定义排序，再按更新时间倒序
        order_by = [Album.sort_order.desc(), Album.updated_at.desc()]
    else:
        # 用户选择的排序
        sort_column = getattr(Album, sort_by, Album.updated_at)
        if order == "asc":
            order_by = [sort_column.asc()]
        else:
            order_by = [sort_column.desc()]
    
    # 获取相册列表（只显示未删除的）
    albums_result = await db.execute(
        select(Album)
        .where(Album.is_deleted == False)
        .order_by(*order_by)
    )
    albums = albums_result.scalars().all()
    
    # 为每个相册计算照片数量
    albums_with_count = []
    for album in albums:
        photo_count_result = await db.execute(
            select(func.count(Photo.id)).where(Photo.album_id == album.id)
        )
        photo_count = photo_count_result.scalar() or 0
        albums_with_count.append({
            "album": album,
            "photo_count": photo_count
        })
    
    return templates.TemplateResponse("albums.html", {
        "request": request,
        "albums": albums_with_count,
        "current_sort": sort_by,
        "current_order": order
    })


@router.post("/albums/create", summary="创建新相册")
async def create_album(
    name: str = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """创建新相册"""
    album = Album(name=name, description=description)
    db.add(album)
    await db.commit()
    return RedirectResponse(url="/admin/albums", status_code=303)


@router.post("/album/{album_id}/edit", summary="编辑相册")
async def edit_album(
    album_id: int,
    name: str = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """编辑相册信息"""
    album_result = await db.execute(
        select(Album).where(Album.id == album_id)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    album.name = name
    album.description = description
    await db.commit()
    
    return RedirectResponse(url=f"/admin/album/{album_id}", status_code=303)


@router.post("/album/{album_id}/delete", summary="删除相册")
async def delete_album(album_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """删除相册（移入回收站）"""
    # 获取相册信息
    album_result = await db.execute(
        select(Album).where(Album.id == album_id, Album.is_deleted == False)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    # 获取该相册下的所有照片
    photos_result = await db.execute(
        select(Photo).where(Photo.album_id == album_id, Photo.is_deleted == False)
    )
    photos = photos_result.scalars().all()
    
    # 软删除相册
    album.is_deleted = True
    album.deleted_at = datetime.utcnow()
    
    # 软删除该相册下的所有照片
    for photo in photos:
        photo.is_deleted = True
        photo.deleted_at = datetime.utcnow()
    
    await db.commit()
    
    return RedirectResponse(url="/admin/albums?message=相册已移入回收站", status_code=303)


@router.get("/album/{album_id}", response_class=HTMLResponse, summary="相册详情页面")
async def admin_album_detail(
    request: Request, 
    album_id: int,
    sort_by: str = "default",  # 默认使用自定义排序
    order: str = "desc",  # 默认降序
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """相册详情页面"""
    # 获取相册信息（只显示未删除的）
    album_result = await db.execute(
        select(Album).where(Album.id == album_id, Album.is_deleted == False)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    # 构建照片排序条件
    if sort_by == "default":
        # 默认排序：先按自定义排序，再按创建时间倒序
        order_by = [Photo.sort_order.desc(), Photo.created_at.desc()]
    else:
        # 用户选择的排序
        sort_column = getattr(Photo, sort_by, Photo.created_at)
        if order == "asc":
            order_by = [sort_column.asc()]
        else:
            order_by = [sort_column.desc()]
    
    # 获取照片列表（只显示未删除的）
    photos_result = await db.execute(
        select(Photo)
        .where(Photo.album_id == album_id, Photo.is_deleted == False)
        .order_by(*order_by)
    )
    photos = photos_result.scalars().all()
    photos_data = [photo_to_response(photo) for photo in photos]
    
    # 如果相册没有封面且有照片，自动设置第一张照片为封面
    if not album.cover_image and photos:
        first_photo = photos[0]
        album.cover_image = photo_to_response(first_photo).url
        await db.commit()
    
    return templates.TemplateResponse("album_detail.html", {
        "request": request,
        "album": album,
        "photos": photos_data,
        "current_sort": sort_by,
        "current_order": order
    })


@router.post("/album/{album_id}/upload", summary="上传照片到相册")
async def upload_photos_to_album(
    album_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """批量上传照片到指定相册"""
    # 检查相册是否存在（只检查未删除的）
    album_result = await db.execute(
        select(Album).where(Album.id == album_id, Album.is_deleted == False)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    uploaded_count = 0
    for file in files:
        try:
            validate_file(file)
            filename, file_path, file_size, width, height = await save_uploaded_file(file)
            
            photo = Photo(
                album_id=album_id,
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                width=width,
                height=height
            )
            
            db.add(photo)
            uploaded_count += 1
            
        except Exception as e:
            print(f"上传 {file.filename} 失败: {e}")
            continue
    
    await db.commit()
    return RedirectResponse(url=f"/admin/album/{album_id}", status_code=303)


@router.get("/photos", response_class=HTMLResponse, summary="照片管理页面")
async def admin_photos(
    request: Request, 
    sort_by: str = "default",  # 默认使用自定义排序
    order: str = "desc",  # 默认降序
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """照片管理页面"""
    # 构建排序条件
    if sort_by == "default":
        # 默认排序：先按自定义排序，再按创建时间倒序
        order_by = [Photo.sort_order.desc(), Photo.created_at.desc()]
    else:
        # 用户选择的排序
        sort_column = getattr(Photo, sort_by, Photo.created_at)
        if order == "asc":
            order_by = [sort_column.asc()]
        else:
            order_by = [sort_column.desc()]
    
    # 只显示未删除的照片
    photos_result = await db.execute(
        select(Photo)
        .where(Photo.is_deleted == False)
        .order_by(*order_by)
        .limit(50)
    )
    photos = photos_result.scalars().all()
    photos_data = [photo_to_response(photo) for photo in photos]
    
    return templates.TemplateResponse("photos.html", {
        "request": request,
        "photos": photos_data,
        "current_sort": sort_by,
        "current_order": order
    })


@router.post("/photo/{photo_id}/delete", summary="删除照片")
async def delete_photo(photo_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """删除单张照片（移入回收站）"""
    # 获取照片信息
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.is_deleted == False)
    )
    photo = photo_result.scalar_one_or_none()
    
    if photo:
        album_id = photo.album_id
        
        # 软删除照片
        photo.is_deleted = True
        photo.deleted_at = datetime.utcnow()
        await db.commit()
        
        return RedirectResponse(url=f"/admin/album/{album_id}?message=照片已移入回收站", status_code=303)
    
    return RedirectResponse(url="/admin/photos", status_code=303)


@router.post("/photos/batch-delete", summary="批量删除照片")
async def batch_delete_photos(
    photo_ids: str = Form(...),  # 逗号分隔的照片ID
    album_id: int = Form(None),  # 相册ID，用于重定向
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """批量删除照片（移入回收站）"""
    try:
        # 解析照片ID列表
        id_list = [int(id.strip()) for id in photo_ids.split(',') if id.strip()]
        
        if not id_list:
            raise HTTPException(status_code=400, detail="没有选择要删除的照片")
        
        # 获取所有要删除的照片信息
        photos_result = await db.execute(
            select(Photo).where(Photo.id.in_(id_list), Photo.is_deleted == False)
        )
        photos = photos_result.scalars().all()
        
        deleted_count = 0
        redirect_album_id = album_id
        
        for photo in photos:
            # 记录相册ID用于重定向
            if not redirect_album_id:
                redirect_album_id = photo.album_id
            
            # 软删除照片
            photo.is_deleted = True
            photo.deleted_at = datetime.utcnow()
            deleted_count += 1
        
        await db.commit()
        
        # 重定向到相册页面或照片管理页面
        if redirect_album_id:
            return RedirectResponse(url=f"/admin/album/{redirect_album_id}?message=已将{deleted_count}张照片移入回收站", status_code=303)
        else:
            return RedirectResponse(url=f"/admin/photos?message=已将{deleted_count}张照片移入回收站", status_code=303)
            
    except ValueError:
        raise HTTPException(status_code=400, detail="照片ID格式错误")
    except Exception as e:
        print(f"批量删除照片失败: {e}")
        raise HTTPException(status_code=500, detail="批量删除失败")


@router.post("/photo/{photo_id}/edit", summary="编辑照片信息")
async def edit_photo(
    photo_id: int,
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """编辑照片描述"""
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    photo.description = description
    await db.commit()
    
    # 从 referer 判断返回页面
    return RedirectResponse(url=f"/admin/album/{photo.album_id}", status_code=303)


@router.get("/upload", response_class=HTMLResponse, summary="批量上传页面")
async def admin_upload(request: Request, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """批量上传页面"""
    # 获取所有相册（只显示未删除的）
    albums_result = await db.execute(
        select(Album)
        .where(Album.is_deleted == False)
        .order_by(Album.name)
    )
    albums = albums_result.scalars().all()
    
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "albums": albums
    })


@router.put("/album/{album_id}/cover", summary="设置相册封面")
async def set_album_cover(
    album_id: int,
    cover_data: AlbumCoverRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """设置相册封面"""
    # 检查相册是否存在
    album_result = await db.execute(
        select(Album).where(Album.id == album_id)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    # 检查照片是否存在且属于该相册（只检查未删除的）
    photo_result = await db.execute(
        select(Photo).where(Photo.id == cover_data.cover_photo_id, Photo.album_id == album_id, Photo.is_deleted == False)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在或不属于该相册")
    
    # 设置封面
    album.cover_image = photo_to_response(photo).url
    await db.commit()
    
    return {"message": "封面设置成功", "album_id": album_id, "cover_photo_id": cover_data.cover_photo_id}


@router.put("/album/{album_id}/sort", summary="更新相册排序")
async def update_album_sort_admin(
    album_id: int,
    sort_data: AlbumSortRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """更新相册排序"""
    album_result = await db.execute(
        select(Album).where(Album.id == album_id)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    album.sort_order = sort_data.sort_order
    await db.commit()
    
    return {"message": "排序更新成功", "album_id": album_id, "sort_order": sort_data.sort_order}


@router.put("/photo/{photo_id}/sort", summary="更新照片排序")
async def update_photo_sort_admin(
    photo_id: int,
    sort_data: PhotoSortRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(require_admin_auth)
):
    """更新照片排序"""
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    photo.sort_order = sort_data.sort_order
    await db.commit()
    
    return {"message": "排序更新成功", "photo_id": photo_id, "sort_order": sort_data.sort_order}


# 回收站相关路由
@router.get("/trash", response_class=HTMLResponse, summary="回收站页面")
async def admin_trash(request: Request, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """回收站页面"""
    # 获取已删除的相册
    deleted_albums_result = await db.execute(
        select(Album)
        .where(Album.is_deleted == True)
        .order_by(Album.deleted_at.desc())
    )
    deleted_albums = deleted_albums_result.scalars().all()
    
    # 获取已删除的照片
    deleted_photos_result = await db.execute(
        select(Photo)
        .where(Photo.is_deleted == True)
        .order_by(Photo.deleted_at.desc())
    )
    deleted_photos = deleted_photos_result.scalars().all()
    
    # 为已删除的照片获取相册名称
    photos_data = []
    for photo in deleted_photos:
        album_result = await db.execute(
            select(Album).where(Album.id == photo.album_id)
        )
        album = album_result.scalar_one_or_none()
        album_name = album.name if album else "未知相册"
        
        photos_data.append({
            "id": photo.id,
            "album_id": photo.album_id,
            "album_name": album_name,
            "filename": photo.filename,
            "original_filename": photo.original_filename,
            "file_size": photo.file_size,
            "description": photo.description,
            "deleted_at": photo.deleted_at,
            "url": f"/uploads/{photo.filename}",
            "thumbnail_url": f"/uploads/thumb_{photo.filename}",
            "created_at": photo.created_at
        })
    
    # 统计相册中的照片数量
    albums_data = []
    for album in deleted_albums:
        photo_count_result = await db.execute(
            select(func.count(Photo.id))
            .where(Photo.album_id == album.id, Photo.is_deleted == True)
        )
        photo_count = photo_count_result.scalar()
        
        albums_data.append({
            "id": album.id,
            "name": album.name,
            "description": album.description,
            "cover_image": album.cover_image,
            "photo_count": photo_count,
            "deleted_at": album.deleted_at,
            "created_at": album.created_at
        })
    
    return templates.TemplateResponse("trash.html", {
        "request": request,
        "albums": albums_data,
        "photos": photos_data,
        "total_albums": len(albums_data),
        "total_photos": len(photos_data)
    })


@router.post("/trash/album/{album_id}/restore", summary="恢复相册")
async def restore_album(album_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """从回收站恢复相册"""
    # 获取已删除的相册
    album_result = await db.execute(
        select(Album).where(Album.id == album_id, Album.is_deleted == True)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在或未被删除")
    
    # 恢复相册
    album.is_deleted = False
    album.deleted_at = None
    
    # 恢复该相册下的所有照片
    photos_result = await db.execute(
        select(Photo).where(Photo.album_id == album_id, Photo.is_deleted == True)
    )
    photos = photos_result.scalars().all()
    
    for photo in photos:
        photo.is_deleted = False
        photo.deleted_at = None
    
    await db.commit()
    
    return RedirectResponse(url="/admin/trash?message=相册已恢复", status_code=303)


@router.post("/trash/photo/{photo_id}/restore", summary="恢复照片")
async def restore_photo(photo_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """从回收站恢复照片"""
    # 获取已删除的照片
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.is_deleted == True)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在或未被删除")
    
    # 恢复照片
    photo.is_deleted = False
    photo.deleted_at = None
    
    await db.commit()
    
    return RedirectResponse(url="/admin/trash?message=照片已恢复", status_code=303)


@router.post("/trash/album/{album_id}/delete-permanently", summary="永久删除相册")
async def delete_album_permanently(album_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """永久删除相册（包括所有照片文件）"""
    # 获取已删除的相册
    album_result = await db.execute(
        select(Album).where(Album.id == album_id, Album.is_deleted == True)
    )
    album = album_result.scalar_one_or_none()
    
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在或未被删除")
    
    # 获取该相册下的所有已删除照片
    photos_result = await db.execute(
        select(Photo).where(Photo.album_id == album_id, Photo.is_deleted == True)
    )
    photos = photos_result.scalars().all()
    
    # 删除所有照片文件
    for photo in photos:
        try:
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
            # 删除缩略图
            thumbnail_path = os.path.join(settings.upload_dir, f"thumb_{photo.filename}")
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
        except Exception as e:
            print(f"删除文件失败: {e}")
    
    # 永久删除数据库记录
    await db.execute(delete(Photo).where(Photo.album_id == album_id, Photo.is_deleted == True))
    await db.execute(delete(Album).where(Album.id == album_id, Album.is_deleted == True))
    await db.commit()
    
    return RedirectResponse(url="/admin/trash?message=相册已永久删除", status_code=303)


@router.post("/trash/photo/{photo_id}/delete-permanently", summary="永久删除照片")
async def delete_photo_permanently(photo_id: int, db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """永久删除照片文件"""
    # 获取已删除的照片
    photo_result = await db.execute(
        select(Photo).where(Photo.id == photo_id, Photo.is_deleted == True)
    )
    photo = photo_result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在或未被删除")
    
    # 删除文件
    try:
        if os.path.exists(photo.file_path):
            os.remove(photo.file_path)
        # 删除缩略图
        thumbnail_path = os.path.join(settings.upload_dir, f"thumb_{photo.filename}")
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
    except Exception as e:
        print(f"删除文件失败: {e}")
    
    # 永久删除数据库记录
    await db.execute(delete(Photo).where(Photo.id == photo_id, Photo.is_deleted == True))
    await db.commit()
    
    return RedirectResponse(url="/admin/trash?message=照片已永久删除", status_code=303)


@router.post("/trash/clear", summary="清空回收站")
async def clear_trash(db: AsyncSession = Depends(get_db), _: bool = Depends(require_admin_auth)):
    """清空回收站（永久删除所有已删除的相册和照片）"""
    # 获取所有已删除的照片
    photos_result = await db.execute(
        select(Photo).where(Photo.is_deleted == True)
    )
    photos = photos_result.scalars().all()
    
    # 删除所有照片文件
    deleted_photos_count = 0
    for photo in photos:
        try:
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
            # 删除缩略图
            thumbnail_path = os.path.join(settings.upload_dir, f"thumb_{photo.filename}")
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            deleted_photos_count += 1
        except Exception as e:
            print(f"删除文件失败: {e}")
    
    # 获取已删除的相册数量
    albums_result = await db.execute(
        select(func.count(Album.id)).where(Album.is_deleted == True)
    )
    deleted_albums_count = albums_result.scalar()
    
    # 永久删除数据库记录
    await db.execute(delete(Photo).where(Photo.is_deleted == True))
    await db.execute(delete(Album).where(Album.is_deleted == True))
    await db.commit()
    
    return RedirectResponse(url=f"/admin/trash?message=已清空回收站，删除了{deleted_albums_count}个相册和{deleted_photos_count}张照片", status_code=303)