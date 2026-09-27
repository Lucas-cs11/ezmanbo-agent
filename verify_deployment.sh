#!/bin/bash
# eZmanbo 部署验证脚本

set -e

echo "================================"
echo "eZmanbo 部署验证"
echo "================================"
echo ""

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        echo -e "${GREEN}✓${NC} $service 运行中"
        return 0
    else
        echo -e "${RED}✗${NC} $service 未运行"
        return 1
    fi
}

check_port() {
    local port=$1
    local name=$2
    if ss -tlnp | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC} 端口 $port ($name) 监听中"
        return 0
    else
        echo -e "${RED}✗${NC} 端口 $port ($name) 未监听"
        return 1
    fi
}

check_http() {
    local url=$1
    local name=$2
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name 可访问"
        return 0
    else
        echo -e "${RED}✗${NC} $name 不可访问"
        return 1
    fi
}

echo "1. 检查系统服务"
echo "----------------"
check_service "ezmanbo-backend.service"
check_service "ezmanbo-frontend.service"
check_service "nginx.service"
echo ""

echo "2. 检查端口监听"
echo "----------------"
check_port 8000 "后端"
check_port 3000 "前端"
check_port 80 "Nginx"
echo ""

echo "3. 检查 HTTP 端点"
echo "----------------"
check_http "http://localhost:8000/health" "后端健康检查 (直连)"
check_http "http://localhost/health" "后端健康检查 (Nginx)"
check_http "http://localhost/" "前端页面"
echo ""

echo "4. 检查数据库连接"
echo "----------------"
cd /mnt/data/ezmanbo-agent
source venv/bin/activate
if python3 -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('✓ PostgreSQL 连接正常')
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL 连接正常"
else
    echo -e "${RED}✗${NC} PostgreSQL 连接失败"
fi
echo ""

echo "5. 检查知识库"
echo "----------------"
if [ -d "/mnt/data/ezmanbo-agent/data/chroma_db" ]; then
    count=$(PYTHONPATH=. python3 -c "
from app.rag import RAGStore
store = RAGStore()
print(store.count)
" 2>/dev/null)
    if [ "$count" -gt 0 ]; then
        echo -e "${GREEN}✓${NC} 知识库已初始化 ($count 条记录)"
    else
        echo -e "${YELLOW}⚠${NC} 知识库为空"
    fi
else
    echo -e "${YELLOW}⚠${NC} 知识库未创建"
fi
echo ""

echo "6. 检查嵌入模型"
echo "----------------"
if [ -d "/mnt/data/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2" ]; then
    echo -e "${GREEN}✓${NC} 嵌入模型已下载"
else
    echo -e "${RED}✗${NC} 嵌入模型未找到"
fi
echo ""

echo "7. 磁盘空间"
echo "----------------"
root_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
data_usage=$(df -h /mnt/data | tail -1 | awk '{print $5}' | sed 's/%//')

if [ "$root_usage" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} 根分区使用率: ${root_usage}%"
else
    echo -e "${YELLOW}⚠${NC} 根分区使用率: ${root_usage}% (建议清理)"
fi

if [ "$data_usage" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} 数据分区使用率: ${data_usage}%"
else
    echo -e "${YELLOW}⚠${NC} 数据分区使用率: ${data_usage}%"
fi
echo ""

echo "8. 服务资源使用"
echo "----------------"
ps aux | grep -E "(uvicorn|next-server|nginx: master)" | grep -v grep | awk '{printf "%-20s CPU: %5s%% MEM: %5s%%\n", $11, $3, $4}'
echo ""

echo "================================"
echo "验证完成"
echo "================================"
echo ""
echo "访问方式:"
echo "  前端:   http://3.26.51.29/"
echo "  健康检查: http://3.26.51.29/health"
echo ""
echo "管理命令:"
echo "  sudo systemctl status ezmanbo-backend"
echo "  sudo systemctl status ezmanbo-frontend"
echo "  sudo journalctl -u ezmanbo-backend -f"
echo ""
