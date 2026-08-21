# 考研学习控制台 — VPS 部署与运维

> 本目录文件是**模板**：部署时按需替换域名、端口、用户名后安装到系统路径。
> 运维命令假设目录布局与 systemd 服务名与下文一致。

## 目录布局

```text
/opt/kaoyan-console/
├── repo/                  # git 检出（update.sh 会 reset --hard，勿在此放数据）
│   ├── backend/
│   ├── frontend/
│   └── deploy/            # 本仓库的部署模板（即本目录）
├── venv/                  # Python venv（Python 3.12）
├── web/                   # 前端构建产物，Caddy 的 root（构建成功后由 rsync 切换）
├── data/                  # app.db / app.db-wal / app.db-shm   (0700 kaoyan:kaoyan)
└── backups/               # 每日 .db.gz + .json.gz            (0700 kaoyan:kaoyan)

/etc/kaoyan-console.env    # OPENAI_API_KEY 等                    (0640 root:kaoyan)
/etc/caddy/Caddyfile
/etc/systemd/system/kaoyan-api.service
/etc/systemd/system/kaoyan-backup.{service,timer}
/usr/local/bin/kaoyan-backup.sh
/usr/local/bin/kaoyan-update.sh
```

**关键点**：`data/` 和 `backups/` 在 `repo/` **之外**，`git reset --hard` 永远碰不到数据。

## 一、基础环境（一次性）

```bash
# 1) 系统用户（非 root）
sudo useradd --system --home /opt/kaoyan-console --shell /usr/sbin/nologin kaoyan
sudo mkdir -p /opt/kaoyan-console/{repo,web,data,backups}
sudo chown -R kaoyan:kaoyan /opt/kaoyan-console
sudo chmod 700 /opt/kaoyan-console/data /opt/kaoyan-console/backups

# 2) Python 3.12 与工具
sudo apt update
sudo apt install -y python3.12 python3.12-venv sqlite3 rsync git curl
python3.12 -m venv /opt/kaoyan-console/venv
/opt/kaoyan-console/venv/bin/pip install --upgrade pip

# 3) Node 22（构建前端用；内存 ≤1GB 的 VPS 建议本机构建后 rsync dist/，见「待确认」）
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# 4) 时区（影响备份文件名与日志）
sudo timedatectl set-timezone Asia/Shanghai
timedatectl        # 预期 Time zone: Asia/Shanghai (CST, +0800)

# 5) Caddy（自动 HTTPS）
sudo apt install -y caddy
caddy version      # ≥2.8 用 basic_auth；旧版用 basicauth
```

## 二、拉取代码与安装

```bash
# 1) deploy key：VPS 上生成公钥并加到 GitHub 私有仓（只读 Deploy key）
ssh-keygen -t ed25519 -f ~/.ssh/kaoyan_deploy -N ""
cat ~/.ssh/kaoyan_deploy.pub
git clone <git@github.com:.../kaoyan-study-console.git> /opt/kaoyan-console/repo

# 2) 后端依赖
/opt/kaoyan-console/venv/bin/pip install -r /opt/kaoyan-console/repo/backend/requirements.txt

# 3) 前端构建
cd /opt/kaoyan-console/repo/frontend && npm ci && npm run build
sudo mkdir -p /opt/kaoyan-console/web
sudo rsync -a --delete dist/ /opt/kaoyan-console/web/
sudo chown -R kaoyan:kaoyan /opt/kaoyan-console/web
```

## 三、密钥与环境变量

```bash
sudo install -o root -g kaoyan -m 0640 /dev/null /etc/kaoyan-console.env
sudo tee /etc/kaoyan-console.env >/dev/null <<'EOF'
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
EOF
```

> 服务器上 **API Key 只能在这一个文件里配置**，网页设置页只读。改完需 `sudo systemctl restart kaoyan-api`。

## 四、systemd 服务

```bash
sudo cp deploy/kaoyan-api.service /etc/systemd/system/kaoyan-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now kaoyan-api
systemctl status kaoyan-api        # active (running)
journalctl -u kaoyan-api -n 20     # Uvicorn running on http://127.0.0.1:8018
```

**安全要件**：unit 里 `--host 127.0.0.1` 不能改。检查公网侧不可达：

```bash
sudo ss -ltnp | grep 8018          # 预期只有 127.0.0.1:8018，绝不能是 0.0.0.0:8018
```

## 五、Caddy + HTTPS + Basic Auth

```bash
# 1) 生成口令哈希（只把哈希写进配置，口令本身不落盘）
caddy hash-password --plaintext '你的强口令'

# 2) 替换模板：域名、用户名、哈希
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile    # 预期 Valid configuration
sudo systemctl reload caddy
```

**必做验证**（任一条不符即鉴权被绕过，禁止上线）：

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://你的域名/api/health      # 预期 401
curl -sS -o /dev/null -w '%{http_code}\n' https://你的域名/               # 预期 401
curl -sS -o /dev/null -w '%{http_code}\n' -u 用户名:'口令' https://你的域名/api/health   # 预期 200
```

证书验证：

```bash
echo | openssl s_client -connect 你的域名:443 -servername 你的域名 2>/dev/null | openssl x509 -noout -subject -dates
# 预期 Let's Encrypt 签发，notAfter 约 90 天后；Caddy 自动续期
```

防火墙：

```bash
sudo ufw allow 22,80,443/tcp
sudo ufw enable
```

## 六、备份与更新

```bash
# 安装备份脚本与 timer
sudo cp deploy/backup.sh /usr/local/bin/kaoyan-backup.sh
sudo chmod 750 /usr/local/bin/kaoyan-backup.sh
sudo cp deploy/kaoyan-backup.service /etc/systemd/system/
sudo cp deploy/kaoyan-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now kaoyan-backup.timer
sudo systemctl start kaoyan-backup.service        # 立即跑一次
ls -lh /opt/kaoyan-console/backups/               # 预期一个 .db.gz + 一个 .json.gz

# 恢复演练（必须做过一次，否则备份等于没有）
gunzip -c /opt/kaoyan-console/backups/app-<时间>.db.gz > /tmp/restore-test.db
sqlite3 /tmp/restore-test.db "select count(*) from tasks;"   # 与线上任务数一致
```

更新（一条命令；更新前自动备份）：

```bash
sudo cp deploy/update.sh /usr/local/bin/kaoyan-update.sh
sudo chmod 750 /usr/local/bin/kaoyan-update.sh
sudo tee /etc/sudoers.d/kaoyan-update >/dev/null <<'EOF'
kaoyan ALL=(root) NOPASSWD: /bin/systemctl restart kaoyan-api
EOF
sudo -u kaoyan /usr/local/bin/kaoyan-update.sh
```

> `update.sh` 会 `git reset --hard origin/main`：**不要在服务器上直接改代码**，改动一律提交到 GitHub 后更新。

回滚：`cd /opt/kaoyan-console/repo && git reset --hard <上一个commit>`，然后重跑 update 脚本（或手动 `sudo systemctl restart kaoyan-api` + rsync 旧 dist）。

## 七、常用运维命令

```bash
# 状态
systemctl status kaoyan-api caddy
curl -s http://127.0.0.1:8018/api/health        # db_ok / revision / task_count

# 日志（journald 自带上限，无需 logrotate）
journalctl -u kaoyan-api -n 50 --no-pager
journalctl -u kaoyan-api --since today
journalctl -u caddy -n 50 --no-pager

# 重启
sudo systemctl restart kaoyan-api

# 手动备份
sudo /usr/local/bin/kaoyan-backup.sh

# 数据库直查（只读）
sudo -u kaoyan sqlite3 /opt/kaoyan-console/data/app.db "select count(*) from tasks;"
```

## 八、故障排查

| 现象 | 排查 |
|---|---|
| 页面 401 | Basic Auth 用户名/口令不对，或 `route` 里 `basic_auth` 未在 `handle` 之前（Caddy 2.7 用 `basicauth`） |
| 页面 502 / 接口不通 | `systemctl status kaoyan-api`；8018 是否只绑 127.0.0.1；Caddyfile 反代地址 |
| 证书没签发 | `journalctl -u caddy` 看原因（多为 DNS 未生效/80 端口被占）；确认防火墙放行 80/443 |
| 打开页面只有示例数据 | 服务器是空库（首次播种默认数据）。用设置页「导入 JSON 到服务器」或「从本机旧数据一键迁移」 |
| 数据冲突弹窗 | 多端同时编辑的正常保护：选「加载服务器版本」或「用本机版本覆盖」；页面已自动下载本机版本备份 |
| 数据库锁错误 | WAL 模式 + busy_timeout=5000 已覆盖绝大多数场景；`lsof /opt/kaoyan-console/data/app.db` 看是否有残留进程 |
| 前端构建 OOM | 512MB 内存 VPS 上 `tsc && vite build` 可能爆内存：加 swap（`fallocate -l 2G /swapfile`）或改为本机构建后 rsync dist/ |
| 番茄到点没通知 | 浏览器通知需要 HTTPS；确认域名生效且已到设置页「请求通知权限」 |
| 页面顶部「离线只读」 | 后端不可达；`journalctl -u kaoyan-api` 排查，恢复后页面自动重试同步 |

## 九、待确认项（P3 上线前需要确认）

1. VPS 发行版与版本（决定 Python 3.12 / 3.10 与 Caddy 安装源；默认 Ubuntu 24.04）
2. VPS 内存（`free -h`；默认 ≥2GB；≤1GB 改本机构建 + rsync）
3. VPS 架构（默认 x86_64）
4. 域名已解析到 VPS，且 80/443 未被占用
5. Basic Auth 用户名（默认 `studyowner`）与口令
6. OpenAI 兼容服务的 Key / Base URL / Model（写入 `/etc/kaoyan-console.env`）
7. 本机旧数据的浏览器（迁移前先在设置页导出 JSON，或直接在线上页「一键迁移」）