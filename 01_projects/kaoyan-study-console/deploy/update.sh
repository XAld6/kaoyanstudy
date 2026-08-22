#!/usr/bin/env bash
# 考研学习控制台 — 一键更新脚本模板
# 安装位置：/usr/local/bin/kaoyan-update.sh（属主 root:root，chmod 750，root 执行）
# 用法：
#   update.sh                # 更新到 origin/main 最新
#   update.sh <commit SHA>   # 回滚到指定提交（P1-7：不再被强制拉回最新）
# 注意：git reset --hard 会丢弃服务器上的本地改动 —— 有意为之，不要在服务器上直接改代码。
set -euo pipefail
BASE=/opt/kaoyan-console
TARGET_REVISION="${1:-origin/main}"
cd "$BASE"                                                            # 脱离调用者 CWD（如 /root）
/usr/local/bin/kaoyan-backup.sh                                   # 更新前先备份
cd "$BASE/repo"
git fetch --prune origin && git reset --hard "$TARGET_REVISION"
"$BASE/venv/bin/pip" install -q -r backend/requirements.txt
cd frontend && npm ci && npm run build
rsync -a --delete dist/ "$BASE/web/"                                # 当前已在 frontend/ 内
sudo systemctl restart kaoyan-api
sleep 3
curl -fsS http://127.0.0.1:8018/api/health                        # 烟囱测试，失败则脚本非零退出
echo "更新完成"