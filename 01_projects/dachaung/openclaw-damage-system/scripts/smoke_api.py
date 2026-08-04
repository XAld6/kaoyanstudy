"""Quick API smoke check against a running backend.

Usage:
    python scripts/smoke_api.py
    python scripts/smoke_api.py --base http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get(url: str) -> tuple[int, dict | list | str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            raw = res.read().decode("utf-8", errors="replace")
            try:
                return res.status, json.loads(raw)
            except json.JSONDecodeError:
                return res.status, raw
    except urllib.error.HTTPError as exc:
        return exc.code, str(exc)
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    checks = [
        ("health", f"{base}/api/health"),
        ("system", f"{base}/api/system"),
        ("stats", f"{base}/api/stats"),
        ("records_page", f"{base}/api/records/page?page=1&page_size=5"),
        ("settings", f"{base}/api/settings"),
        ("orphans", f"{base}/api/maintenance/orphans"),
    ]

    print(f"smoke check → {base}")
    ok = 0
    for name, url in checks:
        code, body = get(url)
        status = "OK" if code == 200 else "FAIL"
        if code == 200:
            ok += 1
        detail = ""
        if isinstance(body, dict):
            if name == "health":
                detail = f"v={body.get('version')} status={body.get('status')}"
            elif name == "system":
                detail = f"caps={len(body.get('capabilities') or {})}"
            elif name == "stats":
                detail = f"total={body.get('total')}"
            elif name == "records_page":
                detail = f"items={len(body.get('items') or [])} total={body.get('total')}"
            elif name == "settings":
                detail = f"keys={len(body.get('settings') or {})}"
            elif name == "orphans":
                detail = f"orphans={body.get('orphan_count')}"
        else:
            detail = str(body)[:80]
        print(f"  [{status}] {name:14s} HTTP {code}  {detail}")

    print(f"{ok}/{len(checks)} passed")
    return 0 if ok == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
