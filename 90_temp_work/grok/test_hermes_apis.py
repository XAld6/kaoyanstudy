"""Probe Hermes-configured providers. Does not print secrets."""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

CFG = Path(r"C:\Users\Administrator\AppData\Roaming\cn.org.hermesagent.desktop\runtime\hermes-home\config.yaml")


def http_json(method: str, url: str, headers: dict, body: dict | None = None, timeout: float = 25.0):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return {
                "ok": True,
                "status": resp.status,
                "elapsed": round(time.time() - t0, 2),
                "body_len": len(raw),
                "body_preview": raw[:240].decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as e:
        raw = e.read() if e.fp else b""
        return {
            "ok": False,
            "status": e.code,
            "elapsed": round(time.time() - t0, 2),
            "body_len": len(raw),
            "body_preview": raw[:240].decode("utf-8", errors="replace"),
            "error": f"HTTPError {e.code}",
        }
    except Exception as e:
        return {
            "ok": False,
            "status": None,
            "elapsed": round(time.time() - t0, 2),
            "body_len": 0,
            "body_preview": "",
            "error": f"{type(e).__name__}: {e}",
        }


def test_openai_chat(name: str, base_url: str, api_key: str, model: str):
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "max_tokens": 16,
        "stream": False,
    }
    result = http_json("POST", url, headers, body)
    print(f"[{name}] openai_chat model={model}")
    print(f"  ok={result.get('ok')} status={result.get('status')} elapsed={result.get('elapsed')}s error={result.get('error')}")
    if result.get("body_preview"):
        print(f"  preview={result['body_preview']!r}")
    return result


def test_anthropic(name: str, base_url: str, api_key: str, model: str):
    url = base_url.rstrip("/") + "/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
        "stream": False,
    }
    result = http_json("POST", url, headers, body)
    # Some proxies use Authorization instead
    if not result.get("ok") and result.get("status") in (401, 403, None):
        headers2 = {
            "Authorization": f"Bearer {api_key}",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        result2 = http_json("POST", url, headers2, body)
        # also try without /v1 prefix style
        if not result2.get("ok"):
            url3 = base_url.rstrip("/") + "/messages"
            result3 = http_json("POST", url3, headers2, body)
            # pick best
            candidates = [result, result2, result3]
            result = max(candidates, key=lambda r: (bool(r.get("ok")), r.get("status") or 0))
        else:
            result = result2
    print(f"[{name}] anthropic_messages model={model}")
    print(f"  ok={result.get('ok')} status={result.get('status')} elapsed={result.get('elapsed')}s error={result.get('error')}")
    if result.get("body_preview"):
        print(f"  preview={result['body_preview']!r}")
    return result


def main():
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    results = {}

    # default/primary
    m = cfg["model"]
    name = "PRIMARY " + str(m.get("provider"))
    if m.get("api_mode") == "anthropic_messages":
        results[name] = test_anthropic(name, m["base_url"], m["api_key"], m["default"])
    else:
        results[name] = test_openai_chat(name, m["base_url"], m["api_key"], m["default"])

    for key, p in cfg.get("providers", {}).items():
        name = key
        mode = p.get("api_mode") or p.get("transport")
        model = p.get("model")
        if mode in ("anthropic_messages",):
            results[name] = test_anthropic(name, p["base_url"], p["api_key"], model)
        else:
            results[name] = test_openai_chat(name, p["base_url"], p["api_key"], model)

    print("\n=== SUMMARY ===")
    ok_count = 0
    for k, r in results.items():
        mark = "PASS" if r.get("ok") else "FAIL"
        if r.get("ok"):
            ok_count += 1
        print(f"{mark:4} {k} status={r.get('status')} elapsed={r.get('elapsed')}s err={r.get('error')}")
    print(f"passed {ok_count}/{len(results)}")
    return 0 if ok_count else 1


if __name__ == "__main__":
    sys.exit(main())
