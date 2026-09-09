#!/usr/bin/env python3
"""open-jobs-data 数据获取与搜索脚本 (V3 验证)

来源: https://github.com/ConorsCode/open-jobs-data (每日自动更新, MIT)
用法:
  python3 core/jobs_search.py fetch          # 下载最新 jobs.json 到 data/
  python3 core/jobs_search.py search --keyword python --remote --limit 10
  python3 core/jobs_search.py search --keyword "machine learning" --company Stripe
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

JOBS_URL = "https://raw.githubusercontent.com/ConorsCode/open-jobs-data/main/data/jobs.json"
SUMMARY_URL = "https://raw.githubusercontent.com/ConorsCode/open-jobs-data/main/data/summary.json"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
JOBS_FILE = DATA_DIR / "jobs.json"


def fetch() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[fetch] downloading {JOBS_URL} ...")
    with urllib.request.urlopen(JOBS_URL, timeout=60) as resp:
        data = resp.read()
    JOBS_FILE.write_bytes(data)
    jobs = json.loads(data)
    print(f"[fetch] OK: {len(jobs)} jobs -> {JOBS_FILE} ({len(data)/1024/1024:.1f} MB)")


def load_jobs():
    if not JOBS_FILE.exists():
        print("[warn] data/jobs.json not found, run 'fetch' first")
        sys.exit(1)
    return json.loads(JOBS_FILE.read_text())


def normalize(job: dict) -> dict:
    """归一化为统一 schema(对齐规划中的字段)"""
    locations = job.get("locations") or []
    loc_text = ", ".join(locations)
    return {
        "source": "open-jobs-data",
        "company": job.get("company", ""),
        "title": job.get("title", ""),
        "department": job.get("department"),
        "locations": locations,
        "location_text": loc_text,
        "is_remote": job.get("isRemote"),
        "employment_type": job.get("employmentType"),
        "apply_url": job.get("applyUrl", ""),
        "posted_at": job.get("postedAt"),
        "platform": job.get("platform", ""),
        "job_id": job.get("jobId", ""),
    }


def search(jobs, keyword: str, company: str = "", remote_only: bool = False, limit: int = 10):
    kws = [k.lower() for k in keyword.split(",") if k.strip()]
    out = []
    for raw in jobs:
        j = normalize(raw)
        hay = f"{j['title']} {j['company']} {j['department'] or ''} {j['location_text']}".lower()
        if kws and not all(k in hay for k in kws):
            continue
        if company and company.lower() not in j["company"].lower():
            continue
        if remote_only and j["is_remote"] is not True:
            # isRemote 为 null 时按 location 文本推断
            if "remote" not in j["location_text"].lower() and "anywhere" not in j["location_text"].lower():
                continue
        out.append(j)
        if len(out) >= limit:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description="open-jobs-data 搜索工具")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("fetch")
    sp = sub.add_parser("search")
    sp.add_argument("--keyword", default="", help="逗号分隔关键词,如 'python,ml'")
    sp.add_argument("--company", default="")
    sp.add_argument("--remote", action="store_true")
    sp.add_argument("--limit", type=int, default=10)
    sp.add_argument("--china", action="store_true", help="只看中国/远程相关位置")
    args = ap.parse_args()

    if args.cmd == "fetch":
        fetch()
        return
    if args.cmd == "search":
        jobs = load_jobs()
        results = search(jobs, args.keyword, args.company, args.remote, args.limit)
        print(f"\n[search] keyword='{args.keyword}' company='{args.company}' remote={args.remote} -> {len(results)} results\n")
        for i, j in enumerate(results, 1):
            remote_mark = "🌐" if j["is_remote"] else "  "
            print(f"{i:>2}. [{remote_mark}] {j['title']}")
            print(f"     {j['company']} | {j['location_text']} | {j['employment_type'] or '?'}")
            print(f"     {j['apply_url']}")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
