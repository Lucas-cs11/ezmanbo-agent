# eZmanbo 服务器磁盘空间清理指南

## 🚨 当前状态

**磁盘使用率: 98% (6.5GB / 6.7GB)**
**可用空间: 仅 172 MB ⚠️**

这非常危险！系统可能随时因磁盘满而崩溃。

---

## 📊 空间占用分析

### 主要占用者

| 目录/文件 | 大小 | 说明 | 可清理 |
|----------|------|------|--------|
| `~/.cache/pip` | **2.9 GB** | pip 包下载缓存 | ✅ 可安全清理 |
| `~/ezmanbo-agent` | 941 MB | 项目文件 | ❌ 保留 |
| `~/.npm` | 137 MB | npm 缓存 | ✅ 可清理 |
| `/var/cache` | 150 MB | 系统缓存 | ✅ 可清理 |
| `/var/lib` | 346 MB | 系统库 | ⚠️ 部分可清理 |
| `/snap` | 510 MB | Snap 包 | ⚠️ 谨慎清理 |
| `/usr` | 2.0 GB | 系统程序 | ❌ 保留 |

### 预计可释放空间

- **pip 缓存**: ~2.9 GB ⭐ 
- **npm 缓存**: ~137 MB
- **apt 缓存**: ~50-100 MB
- **系统日志**: ~50-200 MB
- **旧 snap 版本**: ~200-500 MB

**总计可释放: ~3.2-3.7 GB**

清理后可用空间将达到 **~3.4-3.9 GB**

---

## ⚡ 快速清理（推荐）

### 方法 1: 使用自动脚本

```bash
ssh -i /Users/lucas/Documents/Server/web_1.pem ubuntu@3.26.51.29
cd ~
./cleanup_disk.sh
```

### 方法 2: 手动逐步清理

```bash
# 1. 清理 pip 缓存 (释放 2.9 GB) ⭐⭐⭐
rm -rf ~/.cache/pip
# 或使用 pip 命令
pip cache purge

# 2. 清理 npm 缓存 (释放 137 MB)
npm cache clean --force
rm -rf ~/.npm

# 3. 清理 apt 缓存 (释放 50-100 MB)
sudo apt clean
sudo apt autoclean
sudo apt autoremove

# 4. 清理系统日志 (释放 50-200 MB)
sudo journalctl --vacuum-time=7d

# 5. 检查结果
df -h
```

---

## 🔍 深度清理（可选）

如果上述清理后空间仍然不足，可以考虑：

### 清理旧 snap 版本

```bash
# 查看 snap 占用
sudo du -sh /var/lib/snapd/snaps/*

# 清理旧版本（保留最新 2 个版本）
sudo snap set system refresh.retain=2

# 手动清理旧版本
snap list --all | awk '/disabled/{print $1, $3}' | \
  while read snapname revision; do
    sudo snap remove "$snapname" --revision="$revision"
  done
```

### 清理 Docker (如果安装了)

```bash
# 清理未使用的容器、镜像、网络
docker system prune -a
```

### 清理 Node.js 模块（临时）

```bash
# 清理项目的 node_modules，需要时重新安装
cd ~/ezmanbo-agent/frontend/web
rm -rf node_modules

# 需要使用时重新安装
npm install
```

---

## 🛡️ 长期防护措施

### 1. 配置 pip 不缓存

在 `~/.pip/pip.conf` 中添加：
```ini
[global]
no-cache-dir = true
```

或每次安装时使用：
```bash
pip install --no-cache-dir package_name
```

### 2. 配置 npm 减少缓存

```bash
npm config set cache-min 0
```

### 3. 定期清理（添加到 crontab）

```bash
# 编辑 crontab
crontab -e

# 添加每周日凌晨 2 点自动清理
0 2 * * 0 ~/cleanup_disk.sh > /dev/null 2>&1
```

### 4. 设置磁盘使用告警

创建监控脚本 `~/check_disk.sh`:
```bash
#!/bin/bash
USED=$(df / | grep / | awk '{ print $5 }' | sed 's/%//g')
if [ $USED -gt 85 ]; then
  echo "警告: 磁盘使用率 ${USED}%，请及时清理"
fi
```

### 5. 考虑扩容

AWS EBS 卷可以在线扩容：

**在 AWS 控制台:**
1. EC2 → Volumes → 选择卷
2. Actions → Modify Volume → 增加大小（如 8GB → 20GB）
3. 在服务器上执行：
```bash
# 扩展分区
sudo growpart /dev/nvme0n1 1

# 扩展文件系统
sudo resize2fs /dev/nvme0n1p1

# 验证
df -h
```

---

## 📈 推荐配置

### 最小配置
- **根分区**: 20 GB（当前 6.7 GB ❌）
- **Swap**: 2 GB（当前 0 GB ❌）

### 推荐配置
- **根分区**: 40-50 GB
- **Swap**: 4 GB
- **EBS 类型**: gp3 (性能更好)

---

## 🚀 立即执行

### 紧急清理（3分钟）

```bash
ssh -i /Users/lucas/Documents/Server/web_1.pem ubuntu@3.26.51.29

# 快速清理 pip 缓存 (释放 2.9GB)
rm -rf ~/.cache/pip

# 检查结果
df -h
```

预期结果：可用空间从 172 MB → **3.1 GB**

### 完整清理（10分钟）

```bash
cd ~
./cleanup_disk.sh
```

预期结果：可用空间达到 **3.4-3.9 GB**

---

## ⚠️ 注意事项

1. **pip 缓存**: 清理后重新安装包会需要重新下载，但不影响已安装的包
2. **npm 缓存**: 清理后首次安装会稍慢
3. **系统日志**: 只保留最近 7 天，足够调试使用
4. **snap 包**: 谨慎删除，确认不需要再删除

---

## 📊 监控命令

```bash
# 实时监控磁盘使用
watch -n 5 df -h

# 查看最大的 10 个目录
sudo du -ah / | sort -rh | head -20

# 查看最近修改的大文件
sudo find / -type f -size +50M -mtime -7 2>/dev/null
```

---

## 🆘 应急方案

如果清理后空间仍然不足：

1. **临时删除前端构建** (释放 ~200 MB):
   ```bash
   rm -rf ~/ezmanbo-agent/frontend/web/.next
   # 需要时重新构建: npm run build
   ```

2. **删除虚拟环境并重建** (释放 ~500 MB):
   ```bash
   rm -rf ~/ezmanbo-agent/venv
   python3 -m venv venv
   source venv/bin/activate
   pip install --no-cache-dir -r requirements.txt
   ```

3. **考虑 EBS 扩容** (推荐长期方案)

---

**立即行动！磁盘满会导致系统不稳定。**

