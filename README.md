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
cd D:\xm\kaoyan-study-console\frontend
npm.cmd install
npm.cmd run dev
```

后端：

```powershell
cd D:\xm\kaoyan-study-console\backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8018
```

## 功能地图

今日页：

- 添加今日任务、快速模板任务
- 勾选完成、记录实际学习分钟数
- 复盘模板：按当天完成率和未完成任务生成复盘草稿
- 收尾检查：检查复盘、实际时长、明日任务是否准备好
- 明日开局：把未完成任务整理到明天

计划页：

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

- 查看最近 7/14/30 天科目计划时长和实际时长
- 调整各科每周目标小时数

AI 教练：

- 使用最近 7 天任务、今日完成情况和复盘文本生成明日建议
- API 不可用时自动显示本地规则建议

设置页：

- 修改目标日期
- 新增、改名、删除科目
- 调整科目颜色和每周目标
- 配置 OpenAI 兼容 API
- 测试 API 连接
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

建议定期在“设置”页点击“导出 JSON”，尤其是：

- 大量调整计划后
- 导入外部数据前
- 清理浏览器缓存前
- 更换浏览器或设备前

恢复数据时，在“设置”页点击“导入 JSON”即可。

导入 JSON 前，系统会先自动下载一份当前数据备份，文件名形如 `kaoyan-study-backup-before-import-2026-06-10.json`。

## 验证

前端测试和构建：

```powershell
cd D:\xm\kaoyan-study-console\frontend
npm.cmd test
npm.cmd run build
```

后端测试：

```powershell
cd D:\xm\kaoyan-study-console\backend
python -m pytest --basetemp ..\.runtime\pytest-temp
```

`--basetemp` 会把 pytest 临时目录放到项目内，避免 Windows 系统临时目录权限异常。

## 项目结构

```text
kaoyan-study-console/
  frontend/              React + Vite + TypeScript 前端
  backend/               FastAPI 后端
  kaoyan-console.bat     推荐入口：打开中文菜单
  kaoyan-console.ps1     启动、关闭、状态管理脚本
  .runtime/              启动日志、PID、测试临时目录
```
