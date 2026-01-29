#!/bin/bash

# 小宇相册 API 后台服务管理脚本
# 使用方法: ./start_daemon.sh {start|stop|restart|status|logs}

APP_NAME="小宇相册API"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$APP_DIR/app.pid"
LOG_FILE="$APP_DIR/logs/app.log"
ERROR_LOG_FILE="$APP_DIR/logs/error.log"
VENV_PATH="$APP_DIR/venv"
PYTHON_SCRIPT="$APP_DIR/main.py"

# 创建日志目录
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/uploads"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# 检查进程是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 获取进程状态
get_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "运行中 (PID: $PID)"
        return 0
    else
        echo "未运行"
        return 1
    fi
}

# 启动服务
start() {
    echo "========================================"
    echo "🚀 启动 $APP_NAME"
    echo "========================================"
    
    if is_running; then
        warn "服务已在运行中 (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "$VENV_PATH" ]; then
        error "虚拟环境不存在: $VENV_PATH"
        error "请先创建虚拟环境: python -m venv venv"
        return 1
    fi
    
    # 激活虚拟环境
    source "$VENV_PATH/bin/activate"
    
    # 检查Python脚本
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        error "Python脚本不存在: $PYTHON_SCRIPT"
        return 1
    fi
    
    info "激活虚拟环境: $VENV_PATH"
    # info "安装/更新依赖..."
    
    # # 安装依赖，显示更详细的错误信息
    # if ! pip3 install -r requirements.txt >> "$LOG_FILE" 2>&1; then
    #     error "依赖安装失败！"
    #     echo ""
    #     error "详细错误信息:"
    #     tail -20 "$LOG_FILE"
    #     echo ""
    #     error "完整日志: $LOG_FILE"
    #     return 1
    # fi
    
    info "启动服务..."
    
    # 后台启动服务（生产环境不使用--reload）
    nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 \
        >> "$LOG_FILE" 2>> "$ERROR_LOG_FILE" &
    
    PID=$!
    echo $PID > "$PID_FILE"
    
    # 等待一秒检查是否启动成功
    sleep 2
    
    if is_running; then
        log "✅ $APP_NAME 启动成功!"
        info "🌐 服务地址: http://localhost:8000"
        info "📖 API文档: http://localhost:8000/docs"
        info "🔧 管理后台: http://localhost:8000/admin"
        info "📋 进程ID: $PID"
        info "📝 日志文件: $LOG_FILE"
        info "❌ 错误日志: $ERROR_LOG_FILE"
        echo ""
        info "使用以下命令管理服务:"
        info "  查看状态: ./start_daemon.sh status"
        info "  查看日志: ./start_daemon.sh logs"
        info "  停止服务: ./start_daemon.sh stop"
        info "  重启服务: ./start_daemon.sh restart"
        return 0
    else
        error "服务启动失败，查看错误日志: $ERROR_LOG_FILE"
        return 1
    fi
}

# 停止服务
stop() {
    echo "========================================"
    echo "🛑 停止 $APP_NAME"
    echo "========================================"
    
    if ! is_running; then
        warn "服务未运行"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    info "正在停止服务 (PID: $PID)..."
    
    # 优雅停止
    kill $PID
    
    # 等待进程结束
    for i in {1..10}; do
        if ! is_running; then
            log "✅ 服务已停止"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # 强制停止
    warn "强制停止服务..."
    kill -9 $PID 2>/dev/null
    rm -f "$PID_FILE"
    log "✅ 服务已强制停止"
}

# 重启服务
restart() {
    echo "========================================"
    echo "🔄 重启 $APP_NAME"
    echo "========================================"
    
    stop
    sleep 2
    start
}

# 查看状态
status() {
    echo "========================================"
    echo "📊 $APP_NAME 状态"
    echo "========================================"
    
    STATUS=$(get_status)
    if [ $? -eq 0 ]; then
        log "状态: $STATUS"
        
        # 显示更多信息
        PID=$(cat "$PID_FILE")
        CPU_MEM=$(ps -p $PID -o %cpu,%mem --no-headers)
        UPTIME=$(ps -p $PID -o etime --no-headers)
        
        info "CPU/内存: $CPU_MEM"
        info "运行时间: $UPTIME"
        info "日志文件: $LOG_FILE"
        info "错误日志: $ERROR_LOG_FILE"
        
        # 检查端口
        if netstat -tlnp 2>/dev/null | grep -q ":8000.*$PID/" ; then
            log "✅ 端口 8000 正常监听"
        else
            warn "⚠️  端口 8000 未在监听"
        fi
    else
        error "状态: $STATUS"
    fi
}

# 查看日志
logs() {
    echo "========================================"
    echo "📝 $APP_NAME 日志"
    echo "========================================"
    
    if [ "$2" = "error" ]; then
        info "显示错误日志 (按 Ctrl+C 退出):"
        tail -f "$ERROR_LOG_FILE"
    else
        info "显示应用日志 (按 Ctrl+C 退出):"
        tail -f "$LOG_FILE"
    fi
}

# 清理日志
clean_logs() {
    echo "========================================"
    echo "🧹 清理日志文件"
    echo "========================================"
    
    if is_running; then
        error "请先停止服务再清理日志"
        return 1
    fi
    
    info "清理日志文件..."
    > "$LOG_FILE"
    > "$ERROR_LOG_FILE"
    log "✅ 日志文件已清理"
}

# 主函数
main() {
    case "$1" in
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        logs)
            logs "$@"
            ;;
        clean)
            clean_logs
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs|clean}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动服务"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  status  - 查看状态"
            echo "  logs    - 查看日志 (logs error 查看错误日志)"
            echo "  clean   - 清理日志文件"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 