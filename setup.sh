#!/bin/bash
# ============================================================
# eZmanbo — eZ-PLM 智能元器件选型与风险评估 Agent 系统
# 一键环境搭建脚本
# ============================================================
set -e

echo "=========================================="
echo " eZmanbo — 环境搭建"
echo "=========================================="

# --- 0. 检查 Python ---
echo "[1/5] 检查 Python 环境..."
PYTHON=$(which python3 2>/dev/null || which python 2>/dev/null)
if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python，请安装 Python 3.9+"
    exit 1
fi
echo "  ✓ Python: $($PYTHON --version)"

# --- 1. 创建虚拟环境 ---
echo "[2/5] 创建 Python 虚拟环境..."
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
    echo "  ✓ 虚拟环境已创建"
else
    echo "  ✓ 虚拟环境已存在"
fi
source .venv/bin/activate

# --- 2. 安装 Python 依赖 ---
echo "[3/5] 安装 Python 依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  ✓ Python 依赖安装完成"

# --- 3. 配置环境变量 ---
echo "[4/5] 配置环境变量..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ⚠ 已创建 .env，请编辑填写 API 密钥后重新运行"
    echo "    需要填写: EZPLM_API_KEY, OPENAI_API_KEY"
else
    echo "  ✓ .env 已存在"
fi

# --- 4. 构建 RAG 知识库（工程知识 + 数据手册） ---
echo "[5/5] 构建 RAG 知识库..."
PYTHONPATH=. python3 scripts/build_knowledge_base.py 2>/dev/null && echo "  ✓ 工程知识库构建完成" || echo "  ⚠ 知识库构建跳过（可能已存在）"

# 检查是否有数据手册 PDF
PDF_COUNT=$(find docs/datasheets -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PDF_COUNT" -gt 0 ]; then
    echo "  ✓ 数据手册 PDF 已就绪 ($PDF_COUNT 份)"
else
    echo "  ⚠ 未找到数据手册 PDF，运行以下命令下载："
    echo "    PYTHONPATH=. python3 scripts/download_datasheets.py"
fi

# --- 5. 前端依赖 ---
echo ""
echo "--- 前端 (Next.js) ---"
if [ -f "frontend/web/package.json" ]; then
    echo "  如需启动 Web UI，请运行:"
    echo "    cd frontend/web && npm install && npm run dev"
else
    echo "  ℹ Web 前端未就绪，可使用 Streamlit 旧版 UI"
fi

echo ""
echo "=========================================="
echo " ✅ 环境搭建完成！"
echo ""
echo "  启动后端: PYTHONPATH=. python3 -m uvicorn app.main:app --reload --port 8000"
echo "  启动前端: cd frontend/web && npm run dev"
echo "  旧版 UI:  PYTHONPATH=. streamlit run frontend/streamlit_app.py"
echo "=========================================="
