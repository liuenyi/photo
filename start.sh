#!/bin/bash

echo "🏠 家庭相册系统启动脚本"
echo "========================="

# 先杀掉占用8000端口的进程
echo "🧹 清理8000端口占用..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 2

echo "📦 激活虚拟环境..."
cd backend
source venv/bin/activate

echo "🚀 启动后端服务..."
echo "📱 微信小程序请导入 miniprogram 目录"
echo "🌐 管理后台: http://localhost:8000/admin"
echo "📖 API文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo "========================="

# 启动服务
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 