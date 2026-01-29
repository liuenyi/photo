#!/bin/bash

echo "小宇相册 API (Python + FastAPI)"
echo "================================"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "虚拟环境: $VIRTUAL_ENV ✓"
else
    echo "警告: 建议在虚拟环境中运行"
fi

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 创建上传目录
mkdir -p uploads

# 启动服务
echo ""
echo "启动服务..."
echo "服务地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo ""

python main.py 