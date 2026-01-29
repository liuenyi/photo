"""
数据库迁移脚本：添加 sort_order 字段
运行前请确保备份数据库
"""
import asyncio
import sqlite3
from app.config import settings

async def migrate_database():
    """添加 sort_order 字段到现有表"""
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    
    # 使用同步连接进行DDL操作
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经存在 sort_order 字段
        cursor.execute("PRAGMA table_info(albums)")
        album_columns = [column[1] for column in cursor.fetchall()]
        
        if 'sort_order' not in album_columns:
            print("为 albums 表添加 sort_order 字段...")
            cursor.execute("ALTER TABLE albums ADD COLUMN sort_order INTEGER DEFAULT 0")
            
            # 为现有相册设置递增的sort_order
            cursor.execute("SELECT id FROM albums ORDER BY updated_at DESC")
            album_ids = cursor.fetchall()
            for i, (album_id,) in enumerate(album_ids):
                cursor.execute("UPDATE albums SET sort_order = ? WHERE id = ?", 
                             (len(album_ids) - i, album_id))
            
            print(f"已为 {len(album_ids)} 个相册设置 sort_order")
        else:
            print("albums 表已包含 sort_order 字段")
        
        # 检查照片表
        cursor.execute("PRAGMA table_info(photos)")
        photo_columns = [column[1] for column in cursor.fetchall()]
        
        if 'sort_order' not in photo_columns:
            print("为 photos 表添加 sort_order 字段...")
            cursor.execute("ALTER TABLE photos ADD COLUMN sort_order INTEGER DEFAULT 0")
            
            # 为现有照片设置递增的sort_order（按相册分组）
            cursor.execute("SELECT DISTINCT album_id FROM photos")
            album_ids = cursor.fetchall()
            
            total_photos = 0
            for (album_id,) in album_ids:
                cursor.execute("SELECT id FROM photos WHERE album_id = ? ORDER BY created_at DESC", (album_id,))
                photo_ids = cursor.fetchall()
                for i, (photo_id,) in enumerate(photo_ids):
                    cursor.execute("UPDATE photos SET sort_order = ? WHERE id = ?", 
                                 (len(photo_ids) - i, photo_id))
                total_photos += len(photo_ids)
            
            print(f"已为 {total_photos} 张照片设置 sort_order")
        else:
            print("photos 表已包含 sort_order 字段")
        
        conn.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_database()) 