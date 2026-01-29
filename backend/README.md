# 小宇相册 API

> 基于 Python + FastAPI 构建的现代化相册管理 API 服务

## ✨ 功能特性

### 🔐 认证系统
- JWT 令牌认证
- 安全的密码验证
- 用户信息管理

### 📁 相册管理
- 相册的增删改查
- 分页查询支持
- 相册统计信息

### 📷 照片管理
- 照片上传（单文件/批量）
- 自动生成缩略图
- 照片信息查看
- 照片删除功能

### 🎛️ Web 管理后台
- **概览仪表板** - 统计数据与快速操作
- **相册管理** - 创建、查看、管理相册
- **照片管理** - 浏览、删除、批量操作
- **批量上传** - 支持拖拽上传多张照片
- **响应式设计** - 支持桌面和移动端

### 🔧 技术特性
- 异步数据库操作（SQLite + SQLAlchemy）
- 自动 API 文档生成（OpenAPI 3.0）
- 文件上传与图片处理
- CORS 跨域支持
- 静态文件服务

## ✨ 核心功能

### 📸 照片管理
- **批量上传**：支持多文件同时上传，自动生成缩略图
- **🆕 内联编辑**：直接在照片卡片上编辑描述，无需弹窗
- **智能压缩**：自动优化图片大小和格式
- **🆕 自定义排序**：支持拖拽重新排序，优化展示效果
- **批量操作**：支持批量删除和移动

### 📁 相册管理
- **分类整理**：创建多个主题相册
- **🆕 自定义排序**：通过拖拽调整相册展示顺序
- **封面设置**：自动或手动设置相册封面
- **相册编辑**：支持名称和描述的快速编辑

### 🎯 排序系统（🆕）
- **智能优先级**：自定义排序 → 时间倒序 → 用户选择排序
- **拖拽排序**：直观的拖拽界面，实时保存
- **多维排序**：支持按时间、名称、大小等多种方式排序
- **小程序同步**：排序设置自动同步到小程序端

### 🌐 小程序 API
- **RESTful 接口**：标准化的 API 设计
- **🆕 智能排序**：自动应用自定义排序逻辑
- **分页查询**：支持大量数据的分页加载
- **响应式设计**：适配不同设备和网络环境

### 🔐 管理后台
- **Web 界面**：现代化的管理界面
- **🆕 内联编辑**：快速编辑照片描述，提升操作效率
- **实时预览**：上传前预览，确保内容质量
- **🆕 拖拽排序**：直观的排序管理，所见即所得
- **批量上传**：高效的内容管理工具

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip

### 安装启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd photo-api

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python start.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问地址

- **API 服务**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **管理后台**: http://localhost:8000/admin/

## 📖 使用指南

### 管理后台使用

1. **首页概览**
   - 查看相册和照片统计
   - 查看最新相册和照片
   - 快速导航到各功能模块

2. **相册管理**
   - 点击"新建相册"创建新相册
   - 点击相册卡片查看相册详情
   - 在相册详情页上传照片

3. **批量上传**
   - 选择目标相册
   - 拖拽或选择多张照片
   - 支持实时预览
   - 一键批量上传

4. **照片管理**
   - 浏览所有照片
   - 点击照片查看大图
   - 删除不需要的照片
   - 跳转到所属相册

### API 使用

#### 认证
```bash
# 登录获取令牌
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"password":"123456"}'
```

#### 获取相册列表
```bash
curl http://localhost:8000/api/albums/
```

#### 上传照片
```bash
curl -X POST http://localhost:8000/api/upload/single \
  -F "file=@photo.jpg" \
  -F "album_id=1"
```

## 🏗️ 项目结构

```
photo-api/
├── main.py                 # 主应用入口
├── requirements.txt        # 依赖包列表
├── start.py               # 启动脚本
├── start.sh               # Shell 启动脚本
├── app/
│   ├── __init__.py
│   ├── config.py          # 应用配置
│   ├── database.py        # 数据库模型
│   ├── schemas.py         # Pydantic 模型
│   └── routers/           # 路由模块
│       ├── auth.py        # 认证路由
│       ├── albums.py      # 相册路由
│       ├── photos.py      # 照片路由
│       ├── upload.py      # 上传路由
│       └── admin.py       # 管理后台路由
├── templates/             # 前端模板
│   ├── base.html          # 基础模板
│   ├── dashboard.html     # 首页仪表板
│   ├── albums.html        # 相册管理页面
│   ├── album_detail.html  # 相册详情页面
│   ├── photos.html        # 照片管理页面
│   └── upload.html        # 批量上传页面
└── uploads/               # 文件上传目录
    ├── photos/            # 原图
    └── thumbnails/        # 缩略图
```

## ⚙️ 配置说明

主要配置项在 `app/config.py` 中：

```python
class Settings(BaseSettings):
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # 安全配置
    secret_key: str = "your-secret-key"
    default_password: str = "123456"
    
    # 文件上传配置
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
```

## 🔄 Node.js 版本对比

| 特性 | Node.js 版本 | Python 版本 | 
|------|-------------|-------------|
| **开发效率** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **类型安全** | ⭐⭐ (TypeScript) | ⭐⭐⭐⭐⭐ (内置) |
| **文档生成** | ⭐⭐ (手动) | ⭐⭐⭐⭐⭐ (自动) |
| **调试体验** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **生态系统** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **性能** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **学习曲线** | ⭐⭐⭐ | ⭐⭐⭐⭐ |

### Python 版本优势
- ✅ **完整的类型注解** - 编译时错误检查
- ✅ **自动 API 文档** - 无需手动维护
- ✅ **更好的调试信息** - 详细的错误栈
- ✅ **统一的异步模型** - async/await 原生支持
- ✅ **内置验证框架** - Pydantic 数据验证
- ✅ **Web 管理界面** - 可视化管理系统

## 🔧 开发说明

### 添加新功能
1. 在 `app/database.py` 中定义数据模型
2. 在 `app/schemas.py` 中定义 API 模型
3. 在 `app/routers/` 中创建路由文件
4. 在 `main.py` 中注册路由

### 自定义配置
复制 `.env.example` 为 `.env` 并修改配置：
```bash
cp .env.example .env
```

### 数据库迁移
目前使用 SQLite，无需复杂迁移。如需 PostgreSQL：
```python
# 修改 app/config.py 中的数据库 URL
database_url: str = "postgresql://user:pass@localhost/db"
```

## 📝 API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🚀 部署指南

### Docker 部署
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 传统部署
```bash
# 安装依赖
pip install -r requirements.txt

# 生产环境启动
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**小宇相册 API** - 让照片管理更简单 📸✨ 