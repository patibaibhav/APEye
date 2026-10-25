#!/usr/bin/env python3
"""Post-deployment smoke test for APEye (standard library only).

Usage:
  python scripts/aws_smoke_test.py --base-url http://YOUR-ENV.elasticbeanstalk.com --username admin
  python scripts/aws_smoke_test.py --base-url http://... --username admin --traffic

--traffic sends controlled bursts that should trigger all four alert types. Only run it
against YOUR OWN deployment. The password is read from APEYE_SMOKE_PASSWORD or prompted.
"""

import argparse
import getpass
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

RESULTS = []


def call(base, method, path, token=None, body=None, raw_url=None, timeout=30):
    url = raw_url or base.rstrip("/") + path
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read()
    except Exception as exc:  # network problem
        return 0, {}, str(exc).encode()


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def jbody(raw):
    try:
        return json.loads(raw)
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--username", default="admin")
    ap.add_argument("--traffic", action="store_true", help="generate suspicious test traffic")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    password = os.getenv("APEYE_SMOKE_PASSWORD") or getpass.getpass(f"Password for {args.username}: ")

    st, _, raw = call(base, "GET", "/api/health")
    check("health ok and database ok", st == 200 and jbody(raw).get("database") == "ok", f"(HTTP {st})")

    st, _, raw = call(base, "GET", "/")
    check("React index served at /", st == 200 and b'id="root"' in raw, f"(HTTP {st})")
    st, _, raw = call(base, "GET", "/alerts")
    check("deep link /alerts served", st == 200 and b'id="root"' in raw, f"(HTTP {st})")

    st, _, raw = call(base, "GET", "/api/dashboard/summary")
    check("protected endpoint rejects anonymous (401)", st == 401, f"(HTTP {st})")

    st, _, raw = call(base, "POST", "/api/auth/login", body={"username": args.username, "password": password})
    token = jbody(raw).get("access_token")
    check("login returns token", st == 200 and bool(token), f"(HTTP {st})")
    if not token:
        print("Cannot continue without a token."); sys.exit(1)

    st, _, raw = call(base, "GET", "/api/auth/me", token)
    check("/api/auth/me", st == 200 and jbody(raw).get("role") == "ADMIN", f"(HTTP {st})")
    st, _, raw = call(base, "GET", "/api/dashboard/summary", token)
    check("dashboard summary", st == 200, f"(HTTP {st})")

    if args.traffic:
        print("--- sending controlled test traffic to your own deployment ---")
        for i in range(12):  # brute force: more than 10 failed logins
            call(base, "POST", "/api/auth/login", body={"username": "nobody", "password": f"wrong-{i}"})
        for i in range(25):  # reconnaissance: many distinct 404 paths
            call(base, "GET", f"/api/probe/path-{i}")
        for p in ("/api/admin", "/api/.env", "/api/config", "/api/backup"):
            call(base, "GET", p)
        for _ in range(20):  # repeated unauthorized: more than 15 x 401
            call(base, "GET", "/api/dashboard/summary")
        for _ in range(110):  # request rate: more than 100 in 60 s
            call(base, "GET", "/api/auth/me")
        time.sleep(3)
        st, _, raw = call(base, "GET", "/api/alerts?page_size=100", token)
        cats = sorted({a.get("category") for a in jbody(raw).get("items", [])})
        want = {"BRUTE_FORCE", "EXCESSIVE_REQUESTS", "RECONNAISSANCE", "UNAUTHORIZED_ACCESS"}
        check("all four alert categories present", want.issubset(set(cats)), f"(found {cats})")

    st, _, raw = call(base, "GET", "/api/logs?page_size=5", token)
    check("logs endpoint returns rows", st == 200 and jbody(raw).get("total_items", 0) > 0, f"(HTTP {st})")

    st, hdr, raw = call(base, "GET", "/api/exports/logs.csv", token)
    check("logs CSV export", st == 200 and "csv" in str(hdr.get("Content-Type", "")), f"(HTTP {st})")

    now = datetime.now(timezone.utc)
    body = {
        "report_type": "SUMMARY",
        "from": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    st, _, raw = call(base, "POST", "/api/reports/archive", token, body)
    arch = jbody(raw)
    check("archive report", st == 201 and "id" in arch, f"(HTTP {st}, backend={arch.get('storage_backend')})")
    if st == 201:
        st, _, raw = call(base, "GET", f"/api/reports/{arch['id']}/download", token)
        url = jbody(raw).get("url", "")
        check("download link issued", st == 200 and bool(url), f"(HTTP {st})")
        if arch.get("storage_backend") == "s3" and url.startswith("http"):
            st, _, _ = call(base, "GET", None, raw_url=url)
            check("presigned URL downloads the object", st == 200, f"(HTTP {st})")
            st, _, _ = call(base, "GET", None, raw_url=url.split("?")[0])
            check("bare S3 object URL is denied (private bucket)", st in (403, 404), f"(HTTP {st})")

    print(f"\n{sum(RESULTS)}/{len(RESULTS)} checks passed")
    print("Manual checks: CloudWatch log group shows alert_created events; metrics namespace "
          "ApiSecurityMonitor appears; RDS is not reachable from your laptop.")
    sys.exit(0 if all(RESULTS) else 1)


if __name__ == "__main__":
    main()
