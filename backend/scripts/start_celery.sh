#!/bin/bash
# Celery Worker 和 Beat 启动脚本
#
# 开发环境使用: ./scripts/start_celery.sh dev
# 生产环境使用: supervisor 或 systemd

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

MODE=${1:-dev}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}=== PayDay Celery 启动脚本 ===${NC}"
echo "项目目录: $PROJECT_DIR"
echo "模式: $MODE"
echo ""

# 检查虚拟环境
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${RED}错误: 未找到虚拟环境 venv/${NC}"
    echo "请先创建虚拟环境: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
source "$PROJECT_DIR/venv/bin/activate"

# 检查 Celery 是否安装
if ! command -v celery &> /dev/null; then
    echo -e "${RED}错误: Celery 未安装${NC}"
    echo "请先安装: pip install celery"
    exit 1
fi

cd "$PROJECT_DIR"

if [ "$MODE" = "dev" ]; then
    # 开发环境 - 单进程，日志输出到控制台
    echo -e "${YELLOW}启动 Celery Worker (开发模式)...${NC}"
    celery -A app.celery_app worker \
        --loglevel=info \
        --concurrency=2

elif [ "$MODE" = "beat" ]; then
    # 启动 Beat 调度器
    echo -e "${YELLOW}启动 Celery Beat...${NC}"
    celery -A app.celery_app beat \
        --loglevel=info

elif [ "$MODE" = "flower" ]; then
    # 启动 Flower 监控
    echo -e "${YELLOW}启动 Celery Flower 监控...${NC}"
    celery -A app.celery_app flower \
        --port=5555 \
        --broker=$REDIS_URL

else
    echo "用法: $0 [dev|beat|flower]"
    echo ""
    echo "  dev    - 启动 Worker (开发模式，单进程)"
    echo "  beat   - 启动 Beat (定时任务调度器)"
    echo "  flower - 启动 Flower (监控面板)"
    exit 1
fi
