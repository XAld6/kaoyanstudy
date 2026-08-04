# 考研学习控制台

一个本地自用的考研学习网页工具，聚焦“今日任务、执行记录、复盘、计划调整、进度对比、AI 建议”。前端数据保存在浏览器 `localStorage`，API Key 只保存在本地后端配置文件里。

## 一键启动

推荐双击：

```text
kaoyan-console.bat
```

菜单说明：

- `1` 一键启动前端、后端，并打开浏览器
- `2` 保存并关闭服务进程
- `3` 查看前端/后端端口状态
- `4` 退出菜单

默认地址：

- 前端：`http://127.0.0.1:5188`
- 后端：`http://127.0.0.1:8018`

学习数据会自动保存在浏览器里。额外备份请到网页“设置”页点击“导出 JSON”。

## 手动启动

前端：

```powershell
cd D:\xm\01_projects\kaoyan-study-console\frontend
npm.cmd install
npm.cmd run dev
```

后端：

```powershell
cd D:\xm\01_projects\kaoyan-study-console\backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8018
```

## 功能地图

今日页：

- 添加今日任务、快速模板任务
- 勾选完成、记录实际学习分钟数（支持 +15 / +30 / 填满计划）
- 专注计时：正计时 / 番茄（15 / 25 / 45 分钟可选，记住上次选择），绑定任务后结束可自动累加实际时长
- 番茄完成后自动进入 5 分钟休息倒计时（可跳过；休息结束也会提醒）
- 今日专注统计：计时器记入的专注分钟与番茄个数（独立于任务实际时长）
- 键盘快捷键（计时进行中）：空格 暂停/继续 · Enter 结束并记入 · Esc 跳过休息/丢弃（输入框内不触发）
- 计时中顶部常驻条（任意页面可暂停/结束/跳过休息）+ 浏览器标签实时显示剩余/已用时间
- **刷新页面不丢计时**：番茄/正计时/休息进度写入 sessionStorage；离开期间已到点的番茄会按目标分钟记入，并尽量接上剩余休息
- 番茄到点提示音 + 系统通知（设置页可开关并测试）
- 逾期提醒：一键把逾期任务整理到当前日期
- 复盘模板：按当天完成率和未完成任务生成复盘草稿
- 收尾检查：检查复盘、实际时长、明日任务是否准备好
- 一键收尾：补复盘草稿 + 补完成任务时长 + 顺延未完成到明天
- 明日开局：把未完成任务整理到明天
- 刷新页面会记住当前标签页（sessionStorage）

计划页：

- 顶部快捷操作：复制上周、顺延未完成、整理逾期、一键减负、一键补块、生成周报
- 周视图和全部任务视图
- 按科目、优先级、状态筛选
- 复制上周计划到本周
- 批量提前/推后任务日期
- 批量调整可见任务优先级和状态
- 顺延未完成任务
- 本周容量对比和调整建议
- 一键减负：把过重日期的低优先级任务推后
- 一键补块：给偏少科目补一个 60 分钟基础块

进度页：

- 学习热力日历：最近 8/12/16 周实际学习量热力图，点击切换当前日期；显示连续天数与合计
- 查看最近 7/14/30 天科目计划时长和实际时长
- 调整各科每周目标小时数
- 一键生成周报（完成率、分科执行、调整提示、下周三条重点），支持复制与下载 Markdown
- 写入复盘：把周报摘要追加到当前日期复盘（同一周不会重复写入）

AI 教练：

- 使用最近 7 天任务、今日完成情况和复盘文本生成建议
- 固定结构：补哪科 / 砍哪块 / 明日三件事
- API 不可用时自动显示同结构的本地规则建议

设置页：

- 修改目标日期
- 新增、改名、删除科目
- 调整科目颜色和每周目标
- 配置 OpenAI 兼容 API
- 测试 API 连接
- 查看备份状态（最近导出时间、距今天数）
- 导出/导入 JSON 数据

## API 配置

启动前端和后端后，进入“设置”页的“API 配置”区域填写：

```text
API Key: sk-xxxxxxxx
Base URL: https://api.openai.com/v1
Model: gpt-4.1-mini
```

OpenAI 兼容服务也可以使用自己的地址：

```text
Base URL: https://你的服务地址/v1
Model: 该服务支持的模型名
```

配置会保存到：

```text
backend/llm_config.local.json
```

该文件已加入 `.gitignore`，不会写入前端，也不会在页面回显 API Key。保存过 API Key 后，只想修改 `Base URL` 或 `Model` 时，可以把 API Key 输入框留空，后端会保留旧 Key。

## 数据备份

常规使用时，学习数据保存在浏览器 `localStorage`。

导出入口：

- **今日页**：顶部「导出备份」条、任务区「备份」按钮
- **设置页**：「数据备份」卡片、底部「导出 JSON 备份」

系统会记录最近一次导出时间：

- 从未导出：打开时顶部提示「立即备份」
- 超过 7 天：建议更新备份
- 超过 14 天：升级为过期提醒

建议在这些时机导出：

- 大量调整计划后
- 导入外部数据前
- 清理浏览器缓存前
- 更换浏览器或设备前

恢复数据时，在“设置”页点击“导入 JSON”即可。

导入 JSON 前，系统会先自动下载一份当前数据备份，文件名形如 `kaoyan-study-backup-before-import-2026-06-10.json`。

## 验证

前端测试和构建：

```powershell
cd D:\xm\01_projects\kaoyan-study-console\frontend
npm.cmd test
npm.cmd run build
```

后端测试：

```powershell
cd D:\xm\01_projects\kaoyan-study-console\backend
python -m pytest --basetemp ..\.runtime\pytest-temp
```

`--basetemp` 会把 pytest 临时目录放到项目内，避免 Windows 系统临时目录权限异常。

## 项目结构

```text
kaoyan-study-console/
  frontend/              React + Vite + TypeScript 前端
    src/main.tsx         应用状态与页面编排
    src/uiComponents.tsx 可复用 UI 组件
    src/studyCore.ts     学习业务纯函数
    src/focusTimer.ts    专注计时
    src/storage.ts       本地存储与备份
  backend/               FastAPI 后端
  kaoyan-console.bat     推荐入口：打开中文菜单
  kaoyan-console.ps1     启动、关闭、状态管理脚本
  .runtime/              启动日志、PID、测试临时目录
```
