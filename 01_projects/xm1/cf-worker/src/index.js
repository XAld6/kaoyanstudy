const HTML = String.raw`<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>校园外墙巡检 Worker 测试页</title>
  <style>
    :root {
      --bg: #f4f6f8;
      --panel: #ffffff;
      --text: #1f2933;
      --muted: #64748b;
      --line: #dde3ea;
      --primary: #1f7a8c;
      --primary-dark: #155e6f;
      --danger: #d93025;
      --ok: #34a853;
      --warn: #c98900;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    }
    header {
      padding: 26px 24px;
      background: #fff;
      border-bottom: 1px solid var(--line);
    }
    main {
      width: min(1120px, calc(100% - 32px));
      margin: 24px auto 48px;
    }
    h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
    h2 { margin: 0 0 16px; font-size: 18px; }
    p { line-height: 1.7; }
    .subtle { color: var(--muted); margin: 0; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    label { display: block; color: var(--muted); font-size: 14px; margin-bottom: 8px; }
    input[type="url"],
    input[type="text"],
    input[type="file"] {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      background: #fff;
      color: var(--text);
    }
    button {
      min-height: 40px;
      border: 0;
      border-radius: 6px;
      background: var(--primary);
      color: #fff;
      font-weight: 700;
      cursor: pointer;
      padding: 0 14px;
    }
    button.secondary { background: #48566a; }
    button:hover { background: var(--primary-dark); }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
    .status {
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0 10px;
      border-radius: 999px;
      background: #eef2f7;
      color: #48566a;
      font-size: 13px;
      font-weight: 700;
    }
    .status.ok { background: #eaf6ee; color: var(--ok); }
    .status.fail { background: #fdecea; color: var(--danger); }
    .status.warn { background: #fff7e6; color: var(--warn); }
    .result-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .result-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fbfcfd;
    }
    .result-card img {
      width: 100%;
      display: block;
      aspect-ratio: 4 / 3;
      object-fit: cover;
    }
    .result-card div { padding: 12px; }
    pre {
      overflow: auto;
      background: #111827;
      color: #e5e7eb;
      padding: 14px;
      border-radius: 8px;
      max-height: 360px;
    }
    @media (max-width: 820px) {
      .grid,
      .result-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1 id="projectName">校园外墙巡检 Worker 测试页</h1>
    <p class="subtle">用于测试 Cloudflare Workers 域名页面访问本地或公网 FastAPI 后端。</p>
  </header>
  <main>
    <section class="grid">
      <div class="panel">
        <h2>后端连接</h2>
        <label for="apiBase">FastAPI 地址</label>
        <input id="apiBase" type="url" placeholder="http://127.0.0.1:8000">
        <div class="actions">
          <button id="saveApi">保存地址</button>
          <button id="healthCheck" class="secondary">健康检查</button>
        </div>
        <p><span id="healthStatus" class="status warn">未检测</span></p>
      </div>
      <div class="panel">
        <h2>样例识别</h2>
        <label for="sampleName">样例文件名</label>
        <input id="sampleName" type="text" value="sample_05_mixed.jpg">
        <div class="actions">
          <button id="detectSample">识别样例图</button>
          <button id="loadRecords" class="secondary">读取记录</button>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2>上传图片识别</h2>
      <label for="imageFile">选择一张外墙图片</label>
      <input id="imageFile" type="file" accept="image/*">
      <div class="actions">
        <button id="detectUpload">上传识别</button>
      </div>
    </section>

    <section class="grid" style="margin-top:16px;">
      <div class="panel">
        <h2>识别结果</h2>
        <div id="cards" class="result-grid"></div>
      </div>
      <div class="panel">
        <h2>接口返回</h2>
        <pre id="output">等待操作...</pre>
      </div>
    </section>
  </main>
  <script>
    const defaultApiBase = "__DEFAULT_API_BASE__";
    const projectName = "__PROJECT_NAME__";
    const apiBaseInput = document.querySelector("#apiBase");
    const output = document.querySelector("#output");
    const cards = document.querySelector("#cards");
    const healthStatus = document.querySelector("#healthStatus");

    document.querySelector("#projectName").textContent = projectName + " · Worker 测试页";
    apiBaseInput.value = localStorage.getItem("wall-ai-api-base") || defaultApiBase;

    function apiBase() {
      return apiBaseInput.value.replace(/\/+$/, "");
    }

    function show(data) {
      output.textContent = JSON.stringify(data, null, 2);
    }

    function showError(error) {
      output.textContent = error.stack || String(error);
    }

    function renderRecord(record) {
      cards.innerHTML = "";
      if (!record) return;
      const image = document.createElement("img");
      image.src = apiBase() + record.result_path;
      image.alt = "识别结果图";
      const body = document.createElement("div");
      body.innerHTML = "<strong>" + record.original_filename + "</strong><p>" + record.risk_label + " · " + record.detections.length + " 个隐患</p>";
      const card = document.createElement("article");
      card.className = "result-card";
      card.append(image, body);
      cards.append(card);
    }

    async function requestJson(path, options) {
      const response = await fetch(apiBase() + path, options);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "HTTP " + response.status);
      }
      return data;
    }

    document.querySelector("#saveApi").addEventListener("click", () => {
      localStorage.setItem("wall-ai-api-base", apiBase());
      show({ saved_api_base: apiBase() });
    });

    document.querySelector("#healthCheck").addEventListener("click", async () => {
      try {
        const data = await requestJson("/health");
        healthStatus.className = "status ok";
        healthStatus.textContent = "连接正常：" + data.engine;
        show(data);
      } catch (error) {
        healthStatus.className = "status fail";
        healthStatus.textContent = "连接失败";
        showError(error);
      }
    });

    document.querySelector("#detectSample").addEventListener("click", async () => {
      try {
        const form = new FormData();
        form.append("sample", document.querySelector("#sampleName").value);
        const data = await requestJson("/api/detect-sample", { method: "POST", body: form });
        renderRecord(data.record);
        show(data);
      } catch (error) {
        showError(error);
      }
    });

    document.querySelector("#detectUpload").addEventListener("click", async () => {
      try {
        const file = document.querySelector("#imageFile").files[0];
        if (!file) throw new Error("请先选择图片。");
        const form = new FormData();
        form.append("file", file);
        const data = await requestJson("/api/detect", { method: "POST", body: form });
        renderRecord(data.record);
        show(data);
      } catch (error) {
        showError(error);
      }
    });

    document.querySelector("#loadRecords").addEventListener("click", async () => {
      try {
        const data = await requestJson("/api/records");
        renderRecord(data.records[0]);
        show(data);
      } catch (error) {
        showError(error);
      }
    });
  </script>
</body>
</html>`;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return Response.json({
        status: "ok",
        worker: "campus-wall-inspection-test",
        default_api_base: env.DEFAULT_API_BASE,
      });
    }

    const html = HTML
      .replace("__DEFAULT_API_BASE__", escapeHtml(env.DEFAULT_API_BASE || "http://127.0.0.1:8000"))
      .replace("__PROJECT_NAME__", escapeHtml(env.PROJECT_NAME || "校园建筑外墙 AI 图像识别巡检系统"));

    return new Response(html, {
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "no-store",
      },
    });
  },
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
