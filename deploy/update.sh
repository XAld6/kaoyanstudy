#!/usr/bin/env bash
# 考研学习控制台 — 一键更新脚本模板
# 安装位置：/usr/local/bin/kaoyan-update.sh（属主 root:root，chmod 750）
# 执行用户需要 sudoers 窄授权：
#   kaoyan ALL=(root) NOPASSWD: /bin/systemctl restart kaoyan-api
# 注意：git reset --hard 会丢弃 VPS 上的本地改动 —— 有意为之，不要在服务器上直接改代码。
set -euo pipefail
BASE=/opt/kaoyan-console
/usr/local/bin/kaoyan-backup.sh                                   # 更新前先备份
cd "$BASE/repo"
git fetch --prune origin && git reset --hard origin/main
"$BASE/venv/bin/pip" install -q -r backend/requirements.txt
cd frontend && npm ci && npm run build
rsync -a --delete frontend/dist/ "$BASE/web/"                     # 构建成功后才切产物
sudo systemctl restart kaoyan-api
sleep 3
curl -fsS http://127.0.0.1:8018/api/health                        # 烟囱测试，失败则脚本非零退出
echo "更新完成"