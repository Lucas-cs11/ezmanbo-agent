#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, Tuple

API_KEY = ""
BASE_URL = "https://www.ezplm.cn"
PART_KEYWORD = "TPS79301DBVR"
PAGE_SIZE = "10"


def canonical_query(params: Dict[str, Any]) -> str:
    items: list[Tuple[str, str]] = []
    for key, value in params.items():
        if value is None or value == "":
            continue
        items.append((str(key), str(value)))
    items.sort(key=lambda item: (item[0], item[1]))
    return "&".join(
        f"{urllib.parse.quote(key, safe='')}={urllib.parse.quote(value, safe='')}"
        for key, value in items
    )


def build_signature(
    api_key: str,
    method: str,
    path: str,
    params: Dict[str, Any],
    timestamp: str,
    nonce: str,
) -> str:
    canonical = "\n".join(
        [method.upper(), path, canonical_query(params), timestamp, nonce]
    )
    digest = hmac.new(
        api_key.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def request_json(
    base_url: str,
    api_key: str,
    path: str,
    params: Dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    signature = build_signature(api_key, "GET", path, params, timestamp, nonce)
    query = canonical_query(params)
    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{query}"

    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "X-API-Key": api_key,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


def main() -> int:
    api_key = API_KEY.strip()
    base_url = BASE_URL.rstrip("/")
    keyword = PART_KEYWORD
    page_size = PAGE_SIZE

    parts_status, parts_body = request_json(
        base_url,
        api_key,
        "/api/v1/api-key/parts",
        {"keyword": keyword, "pageSize": page_size},
    )
    print("parts_status =", parts_status)
    print(json.dumps(parts_body, ensure_ascii=False, indent=2))

    items = parts_body.get("data", [])
    if not items:
        print("no part returned", file=sys.stderr)
        return 2

    partlib_id = items[0]["id"]
    ref_status, ref_body = request_json(
        base_url,
        api_key,
        "/api/v1/api-key/reference-designs",
        {"partlibId": partlib_id, "pageSize": page_size},
    )
    print("reference_designs_status =", ref_status)
    print(json.dumps(ref_body, ensure_ascii=False, indent=2))
    return 0 if parts_status == 200 and ref_status == 200 else 3


if __name__ == "__main__":
    raise SystemExit(main())
