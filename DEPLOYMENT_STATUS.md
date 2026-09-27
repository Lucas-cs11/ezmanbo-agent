# eZmanbo 部署状态报告

> **⚠️ 本文档是 2026-09-25 的历史快照，已不再维护。** 当前的进度、阻塞项与决策请以
> [`ROADMAP.md`](ROADMAP.md) 为准。文中「入口/认证」部分描述的是加 HTTPS 之前的状态：
> 现在 `https://ezmanbo.online` 才是主入口，`:8088` 只是退路，`/register` 已永久关闭。

**部署时间**: 2026-09-25  
**服务器**: 3.26.51.29 (AWS EC2)

---

## ✅ 已完成的任务

### 1. 磁盘空间优化 ✅
- **问题**: 根分区使用率 95%（6.3G / 6.7G）
- **解决**: 
  - 移动 ~/.cache (2.7GB) 到 /mnt/data
  - 创建软链接指向新位置
  - 根分区使用率降至 55%（3.6G / 6.7G）
  - /mnt/data 有 92GB 可用空间

### 2. 嵌入模型配置 ✅
- **模型**: sentence-transformers/all-MiniLM-L6-v2
- **维度**: 384
- **大小**: 约 80MB
- **位置**: /mnt/data/.cache/huggingface/hub/
- **镜像**: https://hf-mirror.com (中国加速)
- **状态**: 已下载并测试成功

### 3. PostgreSQL 数据库 ✅
- **连接**: database-1.c10sik8soujc.ap-southeast-2.rds.amazonaws.com:5432
- **数据库**: ezmanbo
- **版本**: PostgreSQL 18.3
- **表结构**:
  - users (用户表)
  - admin_config (管理配置)
  - chat_sessions (对话会话)
  - chat_messages (对话消息)
- **状态**: 已连接并初始化

### 4. 知识库构建 ✅
- **存储**: ChromaDB (本地持久化)
- **位置**: /mnt/data/ezmanbo-agent/data/chroma_db/
- **条目数**: 29 条工程知识
- **来源**: data/knowledge/engineering_knowledge.json
- **测试**: 检索功能正常，相关度评分准确

### 5. 依赖包安装 ✅
新增安装的包:
- python-multipart (FastAPI 表单支持)
- psycopg2-binary (PostgreSQL 驱动)
- sentence-transformers + 依赖 (嵌入模型)
  - torch 2.14.0
  - transformers 5.17.0
  - scikit-learn 1.9.1

### 6. 前端构建 ✅
- **框架**: Next.js 14.2.35
- **构建**: 生产模式编译成功
- **页面**: 7 个静态页面
  - / (主页)
  - /login (登录)
  - /register (自助注册已关闭，页面保留为说明页)
  - /setup (设置)
  - /_not-found (404)
- **大小**: First Load JS 87.6 kB (共享) + 页面特定资源

### 7. Nginx 反向代理 ✅
- **版本**: nginx/1.28.3
- **配置**: /etc/nginx/sites-available/ezmanbo
- **路由**:
  - `/health` → 后端健康检查
  - `/api/*` → 后端 API (127.0.0.1:8000)
  - `/*` → 前端 (127.0.0.1:3000)
- **特性**: 
  - SSE 支持 (proxy_buffering off)
  - 10MB 上传限制
  - 300秒读取超时
  - WebSocket 升级支持

### 8. Systemd 服务配置 ✅

**后端服务** (ezmanbo-backend.service):
```bash
sudo systemctl status ezmanbo-backend
# ● ezmanbo-backend.service - eZmanbo FastAPI Backend
#      Active: active (running)
#    Main PID: 24101
#      Memory: 71.5M
```

**前端服务** (ezmanbo-frontend.service):
```bash
sudo systemctl status ezmanbo-frontend
# ● ezmanbo-frontend.service - eZmanbo Next.js Frontend
#      Active: active (running)
#    Main PID: 24341
#      Memory: 61.2M
```

**自动启动**: 已启用，服务器重启后自动恢复

---

## 🧪 测试验证

### 1. 后端健康检查 ✅
```bash
curl http://localhost/health
# {"status":"ok","started_at":1790311889.67,"uptime_s":171}
```

### 2. 前端页面 ✅
```bash
curl http://localhost/ | grep "<title>"
# <title>eZmanbo — 智能元器件选型</title>
```

### 3. 知识库检索 ✅
```bash
PYTHONPATH=. python3 scripts/build_knowledge_base.py --query "12V转5V降压芯片"
# 返回3条相关结果:
# 1. LDO 压差与效率计算 (相关度: 0.468)
# 2. Buck 输入电容与 EMI 设计 (相关度: 0.429)
# 3. Buck 转换器电感选型公式 (相关度: 0.411)
```

### 4. 端口监听 ✅
```bash
ss -tlnp | grep -E "3000|8000|80"
# 0.0.0.0:8000   uvicorn (后端)
# *:3000         next-server (前端)
# *:80           nginx (反向代理)
```

---

## 📊 服务器资源使用

### 磁盘空间
```
文件系统          大小    已用    可用   使用率  挂载点
/dev/root        6.7G    3.6G    3.0G     55%   /
/dev/nvme1n1      98G    1.1G     92G      2%   /mnt/data
```

### 内存使用
- 后端服务: 71.5 MB
- 前端服务: 61.2 MB
- Nginx: 3.2 MB
- **总计**: ~136 MB

### 进程状态
```
 PID    CPU%  MEM%   COMMAND
24101   0.0   1.4    uvicorn (后端)
24341   0.0   1.2    npm run start (前端)
24382   0.0   0.1    nginx (反向代理)
```

---

## 🌐 访问方式

### 外部访问
- **前端**: http://3.26.51.29/
- **后端健康检查**: http://3.26.51.29/health
- **API 文档**: http://3.26.51.29/api/docs (需通过 Nginx 代理配置)

### 本地访问 (SSH 隧道)
```bash
# 本地 → 服务器
ssh -i /path/to/web_1.pem -L 8080:localhost:80 ubuntu@3.26.51.29

# 然后访问 http://localhost:8080
```

---

## 🔧 管理命令

### 服务管理
```bash
# 查看服务状态
sudo systemctl status ezmanbo-backend ezmanbo-frontend nginx

# 重启服务
sudo systemctl restart ezmanbo-backend
sudo systemctl restart ezmanbo-frontend
sudo systemctl reload nginx

# 查看日志
sudo journalctl -u ezmanbo-backend -f
sudo journalctl -u ezmanbo-frontend -f
sudo tail -f /var/log/nginx/access.log
```

### 环境变量
```bash
# 位置: /mnt/data/ezmanbo-agent/.env
cd /mnt/data/ezmanbo-agent
cat .env

# 修改后需重启服务
sudo systemctl restart ezmanbo-backend
```

### 知识库管理
```bash
cd /mnt/data/ezmanbo-agent
source venv/bin/activate

# 重建知识库
PYTHONPATH=. python3 scripts/build_knowledge_base.py --rebuild

# 测试检索
PYTHONPATH=. python3 scripts/build_knowledge_base.py --query "你的查询"

# 查看知识库状态
ls -lh data/chroma_db/
```

---

## 🔐 安全说明

### 认证要求
大多数 API 端点需要 JWT 认证:
```json
{
  "detail": "未提供认证令牌，请先登录"
}
```

首次使用需要:
1. 访问 http://3.26.51.29/setup 完成初始设置
2. 创建管理员账号
3. 配置 eZ-PLM API 密钥和 LLM 设置

### 防火墙规则
当前 AWS 安全组应允许:
- TCP 22 (SSH)
- TCP 80 (HTTP)
- TCP 443 (HTTPS) - 如果配置 SSL

---

## 📝 待优化项

### 1. HTTPS 配置
```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书（需要域名）
sudo certbot --nginx -d your-domain.com
```

### 2. API 路由优化
当前 API 端点在根路径 (如 /classify)，但 Nginx 配置了 /api/ 前缀。
需要统一路由规则或调整 Nginx 配置。

### 3. 监控告警
考虑添加:
- Prometheus + Grafana 监控
- 磁盘空间告警
- 服务健康检查
- 日志轮转配置

### 4. 向量数据库迁移
当前使用 ChromaDB 本地存储。
如需扩展可考虑:
- pgvector (PostgreSQL 扩展)
- Qdrant / Weaviate (独立向量数据库)

---

## 🆘 故障排查

### 后端无法启动
```bash
# 检查端口占用
sudo lsof -i :8000

# 查看详细错误
sudo journalctl -u ezmanbo-backend -n 100

# 测试环境变量
cd /mnt/data/ezmanbo-agent
source venv/bin/activate
python3 test_env.py
```

### 前端无法启动
```bash
# 检查端口占用
sudo lsof -i :3000

# 查看构建状态
cd /mnt/data/ezmanbo-agent/frontend/web
npm run build

# 手动启动测试
NODE_ENV=production npm run start
```

### Nginx 502 错误
```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 测试 Nginx 配置
sudo nginx -t

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 磁盘空间不足
```bash
# 清理 npm 缓存
npm cache clean --force

# 清理 Docker (如果使用)
docker system prune -a

# 清理系统日志
sudo journalctl --vacuum-time=7d
```

---

## 📚 相关文档

- [README.md](README.md) - 项目概述
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 详细部署指南
- [.env](.env) - 环境变量配置
- [test_env.py](test_env.py) - 环境测试脚本

---

**最后更新**: 2026-09-25 04:53 UTC  
**维护人员**: 请更新此文档以反映部署变更
