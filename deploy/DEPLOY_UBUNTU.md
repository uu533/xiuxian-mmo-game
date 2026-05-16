# 修仙游戏 Ubuntu 部署指南

本文档说明如何在 Ubuntu 云服务器上部署修仙 MMO 游戏，供小范围公开试玩。

---

## 一、服务器准备

### 1.1 系统要求

- Ubuntu 22.04 LTS (推荐) 或 20.04 LTS
- 至少 1GB RAM（推荐 2GB+）
- 至少 20GB 磁盘空间

### 1.2 依赖安装

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl git sqlite3 nginx certbot python3-certbot-nginx

# 安装 Python 3.11（推荐）或使用系统默认 Python 3
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### 1.3 开放端口（防火墙）

```bash
# 开放 HTTP/HTTPS（80/443），禁止公网访问 8000
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# 如果使用 ufw: sudo ufw deny 8000/tcp
```

---

## 二、获取代码

### 2.1 克隆仓库

```bash
# 创建部署目录
sudo mkdir -p /opt/xiuxian-game
sudo chown ubuntu:ubuntu /opt/xiuxian-game

# 切换到部署用户
cd /opt/xiuxian-game

# 克隆仓库（替换为你的仓库地址）
git clone https://github.com/your-repo/xiuxian-mmo-game.git app

cd app
```

### 2.2 安装依赖

```bash
# 创建 Python 虚拟环境
python3.11 -m venv /opt/xiuxian-game/venv

# 激活虚拟环境并安装依赖
source /opt/xiuxian-game/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

---

## 三、配置 systemd 服务

### 3.1 复制 service 文件

```bash
sudo cp /opt/xiuxian-game/app/deploy/xiuxian-game.service.example \
   /etc/systemd/system/xiuxian-game.service

# 编辑配置（修改 Domain 和路径）
sudo nano /etc/systemd/system/xiuxian-game.service
```

### 3.2 配置说明

在 service 文件中配置环境变量：

```ini
Environment="ENABLE_DEV_ROUTES=false"
Environment="CORS_ORIGINS=http://your-domain.com"
```

**CORS 配置说明：**
- `ENABLE_DEV_ROUTES=false`：**生产环境必须为 false**，禁用 /dev/* 接口
- `CORS_ORIGINS=http://your-domain.com`：设置为你的域名，允许跨域请求

### 3.3 启动服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start xiuxian-game

# 设置开机自启
sudo systemctl enable xiuxian-game

# 检查状态
sudo systemctl status xiuxian-game
```

---

## 四、配置 Nginx

### 4.1 复制 Nginx 配置

```bash
# 复制配置文件
sudo cp /opt/xiuxian-game/app/deploy/nginx-xiuxian-game.conf.example \
   /etc/nginx/sites-available/xiuxian-game

# 编辑配置
sudo nano /etc/nginx/sites-available/xiuxian-game
```

### 4.2 修改配置

1. 将 `root /opt/xiuxian-game/app/frontend;` 改为实际路径
2. 将 `your-domain.com` 改为你的域名

### 4.3 启用站点

```bash
# 移除默认站点（可选）
sudo rm /etc/nginx/sites-enabled/default

# 启用游戏站点
sudo ln -s /etc/nginx/sites-available/xiuxian-game \
          /etc/nginx/sites-enabled/

# 测试配置并重载 Nginx
sudo nginx -t
sudo systemctl reload nginx
```

---

## 五、服务管理

### 5.1 基本操作

```bash
# 启动
sudo systemctl start xiuxian-game

# 停止
sudo systemctl stop xiuxian-game

# 重启
sudo systemctl restart xiuxian-game

# 查看日志
sudo journalctl -u xiuxian-game -f

# 查看实时日志（最近 100 行）
sudo journalctl -u xiuxian-game -n 100 --no-pager
```

### 5.2 日志清理

```bash
# 清理超过 14 天的 xiuxian-game 单元日志
sudo journalctl --vacuum-time=14d -u xiuxian-game

# 或者限制日志总大小不超过 500MB
sudo journalctl --vacuum-size=500M -u xiuxian-game
```

**注意事项：**
- 不建议手动清空 `/var/log/syslog`，这会影响系统日志和其他服务
- 如需长期日志管理，应配置 `journald` 或使用 `logrotate`
- `journalctl --vacuum-*` 只清理对应服务的日志，不影响系统日志

---

## 六、数据库备份

### 6.1 配置备份脚本

```bash
# 复制备份脚本
cp /opt/xiuxian-game/app/deploy/backup_sqlite.sh \
   /opt/xiuxian-game/backup_sqlite.sh

# 添加执行权限
chmod +x /opt/xiuxian-game/backup_sqlite.sh
```

### 6.2 手动备份

```bash
# 运行备份
cd /opt/xiuxian-game
./backup_sqlite.sh

# 备份位于 /home/ubuntu/xiuxian-backups/
ls -lh /home/ubuntu/xiuxian-backups/
```

### 6.3 自动备份（cron）

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 3 点自动备份
0 3 * * * /opt/xiuxian-game/backup_sqlite.sh >> /var/log/xiuxian-backup.log 2>&1
```

---

## 七、版本更新

### 7.1 更新步骤

```bash
cd /opt/xiuxian-game/app

# 拉取最新代码
git pull origin main

# 激活虚拟环境并重新安装依赖
source /opt/xiuxian-game/venv/bin/activate
pip install -r requirements.txt
deactivate

# 重启服务
sudo systemctl restart xiuxian-game
```

### 7.2 回滚（如遇问题）

```bash
# 查看最近 5 个 commit
cd /opt/xiuxian-game/app
git log --oneline -5

# 回滚到上一个稳定版本（替换为具体 commit）
git revert HEAD  # 或者 git reset --hard <commit>

# 重启服务
sudo systemctl restart xiuxian-game
```

---

## 八、安全注意事项

### 8.1 端口开放

| 端口 | 用途 | 访问 |
|------|------|------|
| 80   | HTTP | 公网   |
| 443  | HTTPS | 公网   |
| 22   | SSH | 仅限管理 IP |
| 8000 | API | **禁止公网** |

### 8.2 /dev/* 路由说明

`/dev/*` 接口（/dev/health、/dev/db-summary、/dev/simulation）默认**禁用**。

生产环境必须设置：
```ini
Environment="ENABLE_DEV_ROUTES=false"
```

### 8.3 临时启用调试路由

如需调试，在 service 文件中临时改为：
```ini
Environment="ENABLE_DEV_ROUTES=true"
```
调试完成后**立即改回 false**。

### 8.4 禁止事项

- 禁止将 `game.db` 放置在公网可访问目录
- 禁止将 `.env` / 密钥文件推送到仓库
- 禁止公网开放 8000 端口
- 禁止使用默认端口和弱密码

---

## 九、故障排查

### 9.1 服务无法启动

```bash
# 查看详细错误日志
sudo journalctl -u xiuxian-game -n 50 --no-pager

# 检查端口占用
sudo lsof -i :8000

# 检查虚拟环境
ls -la /opt/xiuxian-game/venv/bin/python
```

### 9.2 Nginx 502 Bad Gateway

```bash
# 检查后端是否运行
curl http://127.0.0.1:8000/

# 检查 Nginx 日志
sudo tail -f /var/log/nginx/error.log
```

### 9.3 CORS 跨域问题

- 确认 `CORS_ORIGINS` 设置为你的实际域名
- 格式：`http://your-domain.com` 或 `https://your-domain.com`
- 多个域名用逗号分隔：`http://domain1.com,http://domain2.com`

---

## 十、快速参考

```bash
# 启动服务
sudo systemctl start xiuxian-game

# 重启服务
sudo systemctl restart xiuxian-game

# 查看状态
sudo systemctl status xiuxian-game

# 查看日志
sudo journalctl -u xiuxian-game -f

# 更新版本
cd /opt/xiuxian-game/app && git pull && sudo systemctl restart xiuxian-game

# 备份数据库
/opt/xiuxian-game/backup_sqlite.sh

# 启用 HTTPS（需要域名）
sudo certbot --nginx -d your-domain.com
```