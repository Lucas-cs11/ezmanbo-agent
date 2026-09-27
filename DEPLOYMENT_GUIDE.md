# eZmanbo 服务器部署指南

## ✅ 已完成的步骤

### 1. 项目迁移 ✅
- 源代码已上传到: `~/ezmanbo-agent/`
- 文件数: 125 个核心文件
- 大小: 2.1 MB (已排除 .git, .venv, node_modules)

### 2. 依赖安装 ✅

**Python 环境:**
- Python 3.14.4
- 虚拟环境: `~/ezmanbo-agent/venv/`
- 核心包: FastAPI, LangChain, ChromaDB, SQLAlchemy, Uvicorn

**Node.js 环境:**
- Node.js v20.20.2
- npm 10.8.2
- 前端依赖: 584 packages (Next.js 14 + React 18)

### 3. 环境变量配置 ✅
- `.env` 文件已创建
- 包含: eZ-PLM API, DeepSeek LLM, PostgreSQL 连接

### 4. 数据库连接 ✅
- PostgreSQL 客户端已安装
- RDS 连接已验证
- 端点: database-1.c10sik8soujc.ap-southeast-2.rds.amazonaws.com

---

## 🔧 待执行的步骤

### 步骤 1: 安装 PostgreSQL Python 驱动

```bash
# SSH 连接到服务器
ssh -i /Users/lucas/Documents/Server/web_1.pem ubuntu@3.26.51.29

# 激活虚拟环境并安装驱动
cd ~/ezmanbo-agent
source venv/bin/activate
pip install psycopg2-binary

# 验证安装
python3 -c "import psycopg2; print('✅ psycopg2 安装成功')"
```

### 步骤 2: 创建 ezmanbo 数据库

```bash
# 连接到 PostgreSQL
psql -h database-1.c10sik8soujc.ap-southeast-2.rds.amazonaws.com \
     -p 5432 \
     -U postgres \
     -d postgres

# 在 psql 提示符中执行
CREATE DATABASE ezmanbo ENCODING 'UTF8';
\l  -- 列出所有数据库，验证创建成功
\c ezmanbo  -- 切换到新数据库
\q  -- 退出
```

### 步骤 3: 初始化数据库表

```bash
cd ~/ezmanbo-agent
source venv/bin/activate

# 运行数据库迁移（创建表结构）
python3 << 'EOF'
from app.database import init_db
init_db()
print("✅ 数据库表已创建")
EOF
```

### 步骤 4: 测试环境配置

```bash
# 运行测试脚本
python3 test_env.py

# 预期输出应该显示:
# ✅ 所有环境变量已配置
# ✅ 数据库连接成功
# ✅ ezmanbo 数据库已存在
```

### 步骤 5: 构建知识库 (首次部署)

```bash
# 构建 ChromaDB 向量知识库
PYTHONPATH=. python3 scripts/build_knowledge_base.py

# 这会创建 data/chroma_db/ 目录
```

### 步骤 6: 启动后端服务 (测试)

```bash
cd ~/ezmanbo-agent
source venv/bin/activate

# 测试启动
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 在另一个终端测试
curl http://localhost:8000/health

# 预期输出: {"status":"ok","started_at":...}
```

### 步骤 7: 构建前端

```bash
cd ~/ezmanbo-agent/frontend/web

# 构建生产版本
npm run build

# 预期生成 .next/ 目录
```

### 步骤 8: 配置 Nginx (生产部署)

```bash
# 安装 Nginx
sudo apt install -y nginx

# 创建配置文件
sudo nano /etc/nginx/sites-available/ezmanbo
```

粘贴以下配置:

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name 3.26.51.29;  # 或你的域名
    
    client_max_body_size 10M;
    
    # 后端 API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # SSE 支持
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://backend;
    }
    
    # 前端
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/ezmanbo /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

### 步骤 9: 配置 Systemd 服务 (自动启动)

**后端服务:**

```bash
sudo nano /etc/systemd/system/ezmanbo-backend.service
```

```ini
[Unit]
Description=eZmanbo FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ezmanbo-agent
Environment="PATH=/home/ubuntu/ezmanbo-agent/venv/bin"
EnvironmentFile=/home/ubuntu/ezmanbo-agent/.env
ExecStart=/home/ubuntu/ezmanbo-agent/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**前端服务:**

```bash
sudo nano /etc/systemd/system/ezmanbo-frontend.service
```

```ini
[Unit]
Description=eZmanbo Next.js Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ezmanbo-agent/frontend/web
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable ezmanbo-backend ezmanbo-frontend
sudo systemctl start ezmanbo-backend ezmanbo-frontend

# 检查状态
sudo systemctl status ezmanbo-backend
sudo systemctl status ezmanbo-frontend
```

### 步骤 10: 配置防火墙

```bash
# 允许 HTTP/HTTPS 和 SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

---

## 🧪 验证部署

### 1. 后端 API 测试

```bash
# 健康检查
curl http://3.26.51.29/health

# 测试分类接口
curl -X POST http://3.26.51.29/api/classify \
  -H "Content-Type: application/json" \
  -d '{"user_input": "12V转5V降压芯片"}'
```

### 2. 前端访问

浏览器访问: `http://3.26.51.29`

### 3. 日志查看

```bash
# 后端日志
sudo journalctl -u ezmanbo-backend -f

# 前端日志
sudo journalctl -u ezmanbo-frontend -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 服务器资源监控

```bash
# 磁盘使用
df -h

# 内存使用
free -h

# 进程状态
ps aux | grep -E "uvicorn|node"

# 端口占用
ss -tlnp | grep -E "8000|3000|80"
```

---

## 🔄 更新部署

```bash
# 拉取最新代码 (如果使用 git)
cd ~/ezmanbo-agent
git pull

# 安装新依赖
source venv/bin/activate
pip install -r requirements.txt

cd frontend/web
npm install
npm run build

# 重启服务
sudo systemctl restart ezmanbo-backend ezmanbo-frontend
```

---

## 🐛 故障排查

### 后端无法启动

```bash
# 检查环境变量
cd ~/ezmanbo-agent
source venv/bin/activate
python3 test_env.py

# 检查数据库连接
psql -h database-1.c10sik8soujc.ap-southeast-2.rds.amazonaws.com -U postgres -d ezmanbo -c "SELECT 1;"

# 手动启动查看错误
cd ~/ezmanbo-agent
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端无法启动

```bash
# 检查构建
cd ~/ezmanbo-agent/frontend/web
npm run build

# 手动启动
npm run start
```

### 数据库连接超时

检查安全组规则，确保 EC2 (172.31.46.91) 可以访问 RDS 端口 5432。

---

## 📚 相关文件

- `.env`: 环境变量配置
- `test_env.py`: 环境测试脚本
- `requirements.txt`: Python 依赖
- `frontend/web/package.json`: 前端依赖

---

## 🆘 需要帮助？

- 后端日志: `sudo journalctl -u ezmanbo-backend -n 100`
- 前端日志: `sudo journalctl -u ezmanbo-frontend -n 100`
- 数据库日志: AWS RDS 控制台

