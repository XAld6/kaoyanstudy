from pathlib import Path
from datetime import datetime, timezone
import json
import shutil

home = Path(r"C:\Users\Administrator\AppData\Roaming\cn.org.hermesagent.desktop\runtime\hermes-home")
auth = home / "auth.json"
corrupt = home / "auth.json.corrupt"
ts = datetime.now().strftime("%Y%m%d-%H%M%S")
bak = home / f"auth.json.bak-{ts}"

shutil.copy2(auth, bak)
print("backed up to", bak)

old = json.loads(auth.read_text(encoding="utf-8"))
print("old pool keys:", list(old.get("credential_pool", {}).keys()))

# Rebuild ASCII-only store so GBK open() on Chinese Windows works.
# Secrets remain in config.yaml; this file is a status index.
new = {
    "version": 1,
    "providers": {},
    "credential_pool": {
        "custom:api-aijws-com": [
            {
                "id": "3fc9a6",
                "label": "jarvis-grok",
                "auth_type": "api_key",
                "priority": 0,
                "source": "config:api-aijws-com",
                "last_status": None,
                "last_status_at": None,
                "last_error_code": None,
                "last_error_reason": None,
                "last_error_message": None,
                "last_error_reset_at": None,
                "base_url": "https://api.aijws.com",
                "request_count": 0,
                "secret_fingerprint": "sha256:fd0d311155a5e547",
            }
        ],
        "deepseek": [
            {
                "id": "deepseek-1",
                "label": "DeepSeek",
                "auth_type": "api_key",
                "priority": 0,
                "source": "config:deepseek",
                "last_status": None,
                "last_status_at": None,
                "last_error_code": None,
                "last_error_reason": None,
                "last_error_message": None,
                "last_error_reset_at": None,
                "base_url": "https://api.deepseek.com",
                "request_count": 0,
            }
        ],
        "custom:api-look2eye-com": [
            {
                "id": "look2eye-1",
                "label": "look2eye",
                "auth_type": "api_key",
                "priority": 0,
                "source": "config:api-look2eye-com",
                "last_status": None,
                "last_status_at": None,
                "last_error_code": None,
                "last_error_reason": None,
                "last_error_message": None,
                "last_error_reset_at": None,
                "base_url": "https://api.look2eye.com/v1",
                "request_count": 0,
            }
        ],
        "custom:api-wanfeng-me": [
            {
                "id": "wanfeng-1",
                "label": "fuli",
                "auth_type": "api_key",
                "priority": 0,
                "source": "config:api-wanfeng-me",
                "last_status": None,
                "last_status_at": None,
                "last_error_code": None,
                "last_error_reason": None,
                "last_error_message": None,
                "last_error_reset_at": None,
                "base_url": "https://api.zicc.cc/v1",
                "request_count": 0,
            }
        ],
        "custom:maas-api-cn-huabei-1-xf-yun-com": [
            {
                "id": "xunfei-1",
                "label": "xunfei-qwen",
                "auth_type": "api_key",
                "priority": 0,
                "source": "config:maas-api-cn-huabei-1-xf-yun-com",
                "last_status": None,
                "last_status_at": None,
                "last_error_code": None,
                "last_error_reason": None,
                "last_error_message": None,
                "last_error_reset_at": None,
                "base_url": "https://maas-api.cn-huabei-1.xf-yun.com/v2",
                "request_count": 0,
            }
        ],
    },
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

payload = json.dumps(new, ensure_ascii=True, indent=2) + "\n"
auth.write_bytes(payload.encode("ascii"))
print("wrote auth.json, size", auth.stat().st_size)

raw = auth.read_bytes()
for enc in ("utf-8", "gbk", "gb18030", "cp936"):
    t = raw.decode(enc)
    d = json.loads(t)
    print(f"decode {enc}: OK, pool keys={list(d['credential_pool'].keys())}")

if corrupt.exists():
    corrupt_bak = home / f"auth.json.corrupt.bak-{ts}"
    shutil.move(str(corrupt), str(corrupt_bak))
    print("moved old corrupt to", corrupt_bak)

print("AUTH FIX DONE")
