# 计划执行对照表（PLAN COVERAGE）

> 依据：`devops-synchronous-abelson.md`（上级制定计划）
> 仓库：`kaoyan-study-console` 独立仓（main 分支）
> 图例：✅ 完成并有验证证据 / ⏳ 模板就绪、待 VPS 安装 / ➖ 计划未要求或有意延后

## 1) 优化点清单

### 高优先级

| 项 | 状态 | 实现位置 | 验证证据 |
|---|---|---|---|
| H1 SQLite 持久化数据层 | ✅ | `backend/app/db.py`（WAL/busy_timeout/每请求连接/`.backup` API）、`backend/app/state.py`（校验镜像前端、replace 单事务、merge 幂等） | pytest 20/20；冒烟：5 张表 + journal_mode=wal |
| H2 前端数据流异步化（只读缓存兜底） | ✅ | `frontend/src/remoteStore.ts`、`main.tsx` 水合/状态机；storage 改只读缓存键 `cache:v1` | vitest 98/98；E2E online/offline/conflict 18/18 |
| H3 localStorage → 服务端迁移路径 | ✅ | `POST /api/state/import`（replace/merge、兼容裸 AppData、pre-import 快照）+ 设置页「一键迁移/导入到服务器」 | 幂等测试（replace/merge 双模式）；E2E 导入链路 |
| H4 Basic Auth + HTTPS + 后端只绑 127.0.0.1 | ⏳ | `deploy/Caddyfile`（route 内 basic_auth 先行）、`deploy/kaoyan-api.service`（`--host 127.0.0.1` + 加固） | 模板齐备；P3 上服务器后按验证命令执行 |
| H5 CORS 收敛 | ✅ | `main.py`：仅 `KAOYAN_DEV_CORS=1` 时注册 CORSMiddleware | 代码 grep + pytest 全绿 |
| H6 前端生产构建与静态托管 | ✅ | vite build + `deploy/update.sh`（rsync 到独立 `web/` 目录，构建成功后才切换；`npm ci` 不含 `--omit=dev`） | 构建通过（309 KB bundle）；Caddyfile `root/try_files` |
| H7 密钥仅 EnvironmentFile，关闭网页写 Key | ✅ | `POST /api/config` → 403；`/etc/kaoyan-console.env` 模板（0640 root:kaoyan）；GET/test 保留 | 测试 403×2 + 冒烟 403 + 中文提示 |
| H8 SQLite 备份 | ⏳ | `deploy/backup.sh`（`.backup` + gzip + JSON 双份 + 30 天保留）、`kaoyan-backup.{service,timer}` | 模板就绪；每日 03:17；恢复演练随 P3/P5 安装执行 |

### 中优先级

| 项 | 状态 | 实现位置 | 验证证据 |
|---|---|---|---|
| M1 写入去抖 + 冲突保护 | ✅ | `createStateSync`（800ms 合并/串行/flush）+ 409 分支（自动下载本机版本 + 双选择） | remoteStore 单测 12 例；E2E conflict 8/8（含自动下载） |
| M2 AI 接口优化 | ✅ | json.dumps(ensure_ascii=False)；服务端裁剪（today_tasks≤20 / review≤500 / 去 output_format）；max_tokens=400；httpx 四级超时；usage 记日志 | 代码评审 + 全量测试通过 |
| M3 依赖 pin 与 dev 拆分 | ✅ | `pydantic==2.10.4`；`requirements-dev.txt`（pytest） | 服务器 3.12 可复现 |
| M4 测试补充 | ✅ | `test_state_api.py` 10 例 + config 403 改写 + 时区防回归；`remoteStore.test.ts` 12 例；storage 新语义调整 | pytest 20/20；vitest 98/98 |
| M5 时区与日期语义 | ✅ | systemd `Environment=TZ=Asia/Shanghai`；防回归测试断言源码无 `date.today` | 测试通过 |
| M6 systemd 加固与日志轮转 | ⏳ | `kaoyan-api.service`：Restart=always、NoNewPrivileges、ProtectSystem=strict、ReadWritePaths=data+backups；日志走 journald，无需 logrotate | 模板就绪，P3 安装 |
| M7 一键更新脚本 | ✅ | `deploy/update.sh`（备份→reset→pip→npm ci+build→rsync→restart→烟囱测试，`set -e`）| 模板就绪；sudoers 窄授权说明 |
| M8 package.json 元信息与依赖归位 | ➖ 部分 | 已补 name/private/version；构建期依赖挪 devDependencies 按计划降险选项**延后**（npm ci 全量安装不受影响） | — |

### 低优先级

| 项 | 状态 | 说明 |
|---|---|---|
| L1 AI 每日调用上限 | ➖ 未做 | 单用户自用 + Basic Auth 已挡住公网滥用；计划未要求 |
| L2 共享 httpx client | ➖ 未做 | 调用量低，收益有限 |
| L3 健康检查扩展 | ✅ | `/api/health` 含 db_ok / revision / task_count（冒烟已见） |
| L4 前端产物体积 | ➖ 未做 | Caddy zstd/gzip 已开启；bundle 309KB 可接受 |
| L5 Windows 脚本归置 | ✅ | `.bat/.ps1` 保留并注明「仅 Windows 本机」 |

## 2) 分阶段实施

| 阶段 | 状态 | 证据 |
|---|---|---|
| P0 独立出仓 + VPS 基础环境 | ✅（GitHub push ⏳ 待用户） | 独立仓 5 commits；subtree split 保留历史；deploy 模板；基线 82+7 测试 |
| P1-A 后端 SQLite 数据层与 API | ✅ | pytest 20/20 + uvicorn 冒烟（revision/409/403/幂等） |
| P1-B AI 接口与本地规则优化 | ✅ | output_format 移除 + 测试同步修改；其余代码评审 |
| P2 前端接入服务端数据 | ✅ | vitest 98/98 + build；E2E online 7 / offline 3 / conflict 8 |
| P3 systemd + Caddy + HTTPS + Basic Auth 上线 | ⏳ 待用户输入 | 见下「P3 待用户输入」 |
| P5 备份与更新运维 | ⏳ 模板 ✅ | backup.sh/update.sh/timer/service；恢复演练在 P3 后执行 |
| P6 回归测试与中文文档 | ✅（手机端人工回归待上线） | README / deploy/README / docs/迁移说明 / verify_focus_sticky 认证适配 |

## 3) P3 待用户输入（阻塞项）

1. GitHub 私有仓 URL（配置 remote + Deploy key 说明）
2. VPS：SSH 方式、`uname -a && cat /etc/os-release && free -h`、域名（A 记录已解析）
3. Basic Auth 用户名 + 口令（仅生成 bcrypt 哈希）
4. OpenAI Key / Base URL / Model（写入 `/etc/kaoyan-console.env`）
5. 旧数据浏览器：迁移前先导出 JSON（一键迁移入口上线后同样可用）

## 4) 上线后人工回归清单（P6 预留）

- [ ] 今日：加任务/勾完成/+15/+30/填满计划
- [ ] 专注：正计时/番茄 15·25·45/绑定任务自动累加
- [ ] 刷新不丢计时；番茄到点提示音+系统通知（HTTPS）
- [ ] 休息倒计时/跳过/快捷键（空格/Enter/Esc）
- [ ] 计划：复制上周/顺延/整理逾期/一键减负/一键补块
- [ ] 进度：热力图（focusStats 来自服务端）/周报/写入复盘
- [ ] AI：有 Key 三段式；无 Key 回退本地规则
- [ ] 设置：目标日期/科目增删改/导出/导入到服务器
- [ ] 跨设备：电脑改→手机刷新可见，反之亦然
- [ ] 离线只读：停 kaoyan-api → 缓存可见且编辑禁用