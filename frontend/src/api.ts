export type Health = {
  status: string;
  llm_configured: boolean;
  model: string;
  base_url: string;
};

export type ApiForm = {
  api_key: string;
  base_url: string;
  model: string;
};

export type AdviceRequestBody = {
  date: string;
  payload: unknown;
};

export async function readApiBody(response: Response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { detail: text };
  }
}

export async function fetchConfig() {
  const response = await fetch("/api/config");
  const body = await readApiBody(response);
  if (!response.ok) throw new Error(String(body.detail || "读取 API 配置失败"));
  return body as Health;
}

export async function requestAdvice(body: AdviceRequestBody) {
  const response = await fetch("/api/advice", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const result = await readApiBody(response);
  if (!response.ok) throw new Error(String(result.detail || "AI 请求失败"));
  return result as { advice: string[]; source: string };
}

export async function saveConfig(apiForm: ApiForm) {
  const response = await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(apiForm)
  });
  const body = await readApiBody(response);
  if (!response.ok) throw new Error(String(body.detail || "保存失败"));
  return body as Health;
}

export async function testConfig(apiForm: ApiForm) {
  const response = await fetch("/api/config/test", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(apiForm)
  });
  const body = await readApiBody(response);
  if (!response.ok) throw new Error(String(body.detail || "API 测试失败"));
  return body as { message: string; model: string; base_url: string };
}
