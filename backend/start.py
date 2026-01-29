#!/usr/bin/env python3
"""
小宇相册 API 启动脚本
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or version.minor < 8:
        print("错误: 需要 Python 3.8 或更高版本")
        print(f"当前版本: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    else:
        print(f"Python 版本: {version.major}.{version.minor}.{version.micro} ✓")

def check_venv():
    """检查是否在虚拟环境中"""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def install_dependencies():
    """安装依赖"""
    try:
        print("正在安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成 ✓")
    except subprocess.CalledProcessError:
        print("错误: 依赖安装失败")
        sys.exit(1)

def create_upload_dir():
    """创建上传目录"""
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"创建上传目录: {upload_dir} ✓")

def start_server():
    """启动服务器"""
    try:
        print("\n" + "="*50)
        print("启动小宇相册 API 服务...")
        print("="*50)
        print("服务地址: http://localhost:8000")
        print("API 文档: http://localhost:8000/docs")
        print("按 Ctrl+C 停止服务")
        print("="*50 + "\n")
        
        # 启动服务
        subprocess.check_call([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n服务已停止")
    except subprocess.CalledProcessError:
        print("错误: 服务启动失败")
        sys.exit(1)

def main():
    """主函数"""
    print("小宇相册 API 启动器")
    print("-" * 30)
    
    # 检查Python版本
    check_python_version()
    
    # 检查虚拟环境
    if not check_venv():
        print("警告: 建议在虚拟环境中运行")
        response = input("是否继续? (y/N): ")
        if response.lower() != 'y':
            print("已取消启动")
            sys.exit(0)
    else:
        print("虚拟环境: 已激活 ✓")
    
    # 检查依赖文件
    if not os.path.exists("requirements.txt"):
        print("错误: 找不到 requirements.txt 文件")
        sys.exit(1)
    
    # 询问是否安装依赖
    response = input("是否安装/更新依赖? (Y/n): ")
    if response.lower() != 'n':
        install_dependencies()
    
    # 创建必要目录
    create_upload_dir()
    
    # 启动服务
    start_server()

if __name__ == "__main__":
    main() 