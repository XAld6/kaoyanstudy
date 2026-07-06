# Cloudflare Workers 测试页说明

## 作用

`cf-worker/` 是一个独立的 Cloudflare Workers 网页，用于测试公网或本地页面访问校园外墙巡检 FastAPI 后端。

页面支持：

- 健康检查：调用 `/health`。
- 样例识别：调用 `/api/detect-sample`。
- 上传识别：调用 `/api/detect`。
- 历史记录：调用 `/api/records`。

## 本地预览

先启动 FastAPI 后端：

```bash
cd d:\xm\xm1
python scripts\init_db.py
python scripts\generate_samples.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

再启动 Worker：

```bash
cd d:\xm\xm1\cf-worker
npm.cmd install
npm.cmd run dev
```

访问：

```text
http://127.0.0.1:8787
```

## 部署到 Cloudflare

```bash
cd d:\xm\xm1\cf-worker
npm.cmd run deploy
```

首次部署前需要执行 Cloudflare 登录：

```bash
npx.cmd wrangler login
```

## 绑定 CF 域名

编辑 `cf-worker/wrangler.toml`：

```toml
routes = [
  { pattern = "wall-ai.example.com/*", zone_name = "example.com" }
]
```

将 `wall-ai.example.com` 和 `example.com` 替换成你的真实域名。

## 注意事项

- Worker 页面在 Cloudflare 公网域名运行时，不能直接访问你电脑上的 `127.0.0.1:8000`。
- 如果要公网测试，需要把 FastAPI 后端部署到服务器，或使用 Cloudflare Tunnel / 内网穿透暴露一个 HTTPS 地址。
- 后端已开启测试用 CORS，配置位于 `configs/settings.yaml` 的 `server.cors_origins`。
