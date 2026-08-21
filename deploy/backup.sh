#!/usr/bin/env bash
# 考研学习控制台 — 每日备份脚本模板
# 安装位置：/usr/local/bin/kaoyan-backup.sh（chmod 750，属主 root:root 或 kaoyan:kaoyan）
# 注意：WAL 模式下绝不能 cp app.db，必须用 sqlite3 .backup 得到一致快照。
set -euo pipefail
BASE=/opt/kaoyan-console
TS=$(date +%Y%m%d-%H%M)
mkdir -p "$BASE/backups"
sqlite3 "$BASE/data/app.db" ".backup '$BASE/backups/app-$TS.db'"
gzip -f "$BASE/backups/app-$TS.db"
# 直连后端（127.0.0.1 无 Basic Auth），导出网页可直接读回的 JSON
# 空库时 export 返回 404（还没有数据）→ 跳过 JSON 副本，不视为备份失败
if curl -fsS http://127.0.0.1:8018/api/state/export -o "$BASE/backups/app-$TS.json"; then
  gzip -f "$BASE/backups/app-$TS.json"
else
  echo "skip json export: server state empty or unavailable"
fi
find "$BASE/backups" -name 'app-*.gz' -mtime +30 -delete