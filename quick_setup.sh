#!/bin/bash
# eZmanbo 快速设置脚本
# 在服务器上运行此脚本完成剩余配置

set -e

echo "=== eZmanbo 快速设置脚本 ==="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 切换到项目目录
cd ~/ezmanbo-agent

echo -e "${YELLOW}步骤 1/6: 安装 PostgreSQL 驱动...${NC}"
source venv/bin/activate
pip install psycopg2-binary
echo -e "${GREEN}✅ PostgreSQL 驱动已安装${NC}"
echo ""

echo -e "${YELLOW}步骤 2/6: 测试环境配置...${NC}"
python3 test_env.py
echo ""

echo -e "${YELLOW}步骤 3/6: 创建数据库...${NC}"
echo "请手动执行以下命令创建数据库:"
echo ""
echo "psql -h database-1.c10sik8soujc.ap-southeast-2.rds.amazonaws.com -U postgres -d postgres"
echo "然后在 psql 提示符中执行:"
echo "CREATE DATABASE ezmanbo ENCODING 'UTF8';"
echo "\\q"
echo ""
read -p "数据库已创建？按 Enter 继续..."
echo ""

echo -e "${YELLOW}步骤 4/6: 初始化数据库表...${NC}"
python3 << 'EOF'
try:
    from app.database import init_db
    init_db()
    print("✅ 数据库表已创建")
except Exception as e:
    print(f"❌ 数据库初始化失败: {e}")
    print("   请确保 ezmanbo 数据库已创建")
EOF
echo ""

echo -e "${YELLOW}步骤 5/6: 构建知识库...${NC}"
if [ ! -d "data/chroma_db" ]; then
    PYTHONPATH=. python3 scripts/build_knowledge_base.py
    echo -e "${GREEN}✅ 知识库已构建${NC}"
else
    echo -e "${GREEN}✅ 知识库已存在，跳过${NC}"
fi
echo ""

echo -e "${YELLOW}步骤 6/6: 构建前端...${NC}"
cd frontend/web
npm run build
echo -e "${GREEN}✅ 前端已构建${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 设置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "下一步："
echo "1. 测试后端: uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "2. 测试前端: cd frontend/web && npm run start"
echo "3. 配置 Nginx 和 Systemd 服务（参考 DEPLOYMENT_GUIDE.md）"
echo ""
