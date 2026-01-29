# 家庭相册系统

一个温馨的家庭相册管理系统，包含微信小程序前端和Python后端。

## 项目结构

```
photo-album/
├── miniprogram/          # 微信小程序
│   ├── app.js           # 小程序入口文件
│   ├── app.json         # 小程序配置
│   ├── app.wxss         # 全局样式
│   ├── pages/           # 页面文件
│   │   ├── home/        # 首页
│   │   └── album/       # 相册详情页
│   └── project.config.json
├── backend/              # 后端服务
│   ├── app/             # FastAPI应用
│   ├── templates/       # HTML模板
│   ├── uploads/         # 上传文件存储
│   ├── main.py          # 服务器入口
│   └── requirements.txt # Python依赖
├── docs/                # 项目文档
└── README.md           # 项目说明
```

## 快速开始

### 启动后端服务

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 启动微信小程序

1. 打开微信开发者工具
2. 导入 `miniprogram` 目录
3. 配置AppID并预览

## 功能特性

- 📱 **微信小程序** - 温馨家庭风格的相册浏览
- 🖼️ **智能缓存** - 多层缓存提升加载速度
- 📁 **相册管理** - 支持多相册组织照片
- 🔍 **排序功能** - 多种排序方式选择
- 📤 **批量上传** - 支持1000张大容量上传
- 🗂️ **管理后台** - Web界面管理相册和照片

## 技术栈

- **前端**: 微信小程序
- **后端**: Python + FastAPI
- **数据库**: SQLite
- **图片处理**: PIL/Pillow

## 维护者

家庭使用，适合老人操作的简洁设计。 