#!/usr/bin/env python3
"""
verify_1000.py — Re-verify a stratified sample of repositories against the live GitHub API.

Usage:
  python verify_1000.py --input portfolio.csv --out verified_1k.csv --summary verified_1k_summary.json --n 1000

Input CSV expected columns (minimum):
  - owner
  - repo
Optional but helpful for stratified sampling:
  - license_family   (e.g., Permissive, Copyleft, Weak-copyleft, Public-domain, Other, Unknown)
  - language
  - spdx (input SPDX if you have it)
  - stars (input star count if you have it)

Env:
  - GITHUB_TOKEN   (recommended, to avoid low rate limits)
"""
from __future__ import annotations
import argparse, os, sys, time, json, math, random
from typing import Dict, Any, List, Tuple
import requests
import pandas as pd

GITHUB_API = "https://api.github.com"
UA = "ai-github-license-risk/verify_1000"

PERMISSIVE = {
    "MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0", "ISC", "Zlib", "BSL-1.0", "PSF-2.0"
}
COPYLEFT_STRONG = {
    "GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later",
    "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later",
    "AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later"
}
COPYLEFT_WEAK = {
    "LGPL-2.1", "LGPL-2.1-only", "LGPL-2.1-or-later",
    "LGPL-3.0", "LGPL-3.0-only", "LGPL-3.0-or-later",
    "MPL-2.0", "CDDL-1.0", "CDDL-1.1", "EPL-1.0", "EPL-2.0", "CPL-1.0"
}
PUBLIC_DOMAIN = {"Unlicense", "CC0-1.0"}
OTHER_LICENSES = {
    # Put unusual or restrictive SPDX here if you want them grouped as "Other"
    "MS-RL", "MS-PL", "ODbL-1.0", "OSL-3.0", "BSL-1.1"
}

def spdx_to_family(spdx: str | None) -> str:
    if not spdx or spdx in {"NOASSERTION", "NONE"}:
        return "Unknown"
    s = spdx.strip()
    if s in PERMISSIVE: return "Permissive"
    if s in COPYLEFT_STRONG: return "Copyleft"
    if s in COPYLEFT_WEAK: return "Weak-copyleft"
    if s in PUBLIC_DOMAIN: return "Public-domain"
    if s in OTHER_LICENSES: return "Other"
    # Fallback heuristics by name pattern
    if s.startswith("BSD"): return "Permissive"
    if s.startswith("GPL"): return "Copyleft"
    if s.startswith("LGPL") or s.startswith("MPL") or s.startswith("EPL") or s.startswith("CDDL"):
        return "Weak-copyleft"
    return "Other"

def make_session(token: str | None) -> requests.Session:
    sess = requests.Session()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": UA,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    sess.headers.update(headers)
    return sess

def respect_rate_limit(resp: requests.Response):
    # If we hit secondary rate limits or abuse detection, back off briefly
    if resp.status_code == 403:
        reset = resp.headers.get("X-RateLimit-Reset")
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining == "0" and reset:
            wait = max(0, int(reset) - int(time.time())) + 3
            time.sleep(min(wait, 120))  # cap to 2 minutes to keep going
        else:
            time.sleep(2)

def safe_get(sess: requests.Session, url: str, params: Dict[str, Any] | None = None, retries: int = 3) -> requests.Response | None:
    for i in range(retries):
        try:
            r = sess.get(url, params=params, timeout=30)
            if r.status_code in (200, 301, 302):
                return r
            if r.status_code in (403, 429, 500, 502, 503, 504):
                respect_rate_limit(r)
                time.sleep(1.5 * (i + 1))
                continue
            return r  # 404, 451, etc — return anyway to record
        except requests.RequestException:
            time.sleep(1.5 * (i + 1))
    return None

def fetch_repo(sess: requests.Session, full_name: str) -> Tuple[Dict[str, Any] | None, str | None]:
    url = f"{GITHUB_API}/repos/{full_name}"
    r = safe_get(sess, url)
    if r is None:
        return None, "network_error"
    if r.status_code != 200:
        return {"status_code": r.status_code, "message": r.text}, "http_error"
    return r.json(), None

def fetch_latest_commit_sha(sess: requests.Session, owner: str, repo: str, branch: str) -> str | None:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
    r = safe_get(sess, url, params={"sha": branch, "per_page": 1})
    if r is None or r.status_code != 200:
        return None
    js = r.json()
    if isinstance(js, list) and js:
        return js[0].get("sha")
    return None

def stratified_sample(df: pd.DataFrame, n: int, group_cols: List[str]) -> pd.DataFrame:
    df_nondup = df.drop_duplicates(subset=["owner", "repo"]).copy()
    if not group_cols or not all(c in df_nondup.columns for c in group_cols):
        # No stratification info — take random sample
        return df_nondup.sample(n=min(n, len(df_nondup)), random_state=42)
    # Proportional allocation by groups
    groups = df_nondup.groupby(group_cols)
    total = len(df_nondup)
    alloc = {}
    for key, g in groups:
        share = len(g) / total
        alloc[key] = int(math.floor(share * n))
    # Distribute remainder
    assigned = sum(alloc.values())
    remainder = max(0, n - assigned)
    # Choose groups for remainder by largest fractional parts
    fracs = []
    for key, g in groups:
        fracs.append((key, (len(g) / total) * n - alloc[key]))
    fracs.sort(key=lambda x: x[1], reverse=True)
    for i in range(remainder):
        alloc[fracs[i % len(fracs)][0]] += 1
    # Sample from each group
    parts = []
    for key, g in groups:
        k = min(alloc.get(key, 0), len(g))
        if k > 0:
            parts.append(g.sample(n=k, random_state=42))
    if not parts:
        return df_nondup.sample(n=min(n, len(df_nondup)), random_state=42)
    out = pd.concat(parts, ignore_index=True)
    # In rare rounding cases, trim or top-up
    if len(out) > n:
        out = out.sample(n=n, random_state=42)
    elif len(out) < n:
        leftover = df_nondup.drop(out.index, errors="ignore")
        need = min(n - len(out), len(leftover))
        if need > 0:
            out = pd.concat([out, leftover.sample(n=need, random_state=42)], ignore_index=True)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to portfolio.csv")
    ap.add_argument("--out", required=True, help="Path to write verified sample CSV")
    ap.add_argument("--summary", required=True, help="Path to write JSON summary")
    ap.add_argument("--n", type=int, default=1000, help="Sample size (default 1000)")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("WARNING: GITHUB_TOKEN not set; you will hit very low rate limits.", file=sys.stderr)

    df = pd.read_csv(args.input)
    # Normalize input columns
    if "full_name" in df.columns and (("owner" not in df.columns) or ("repo" not in df.columns)):
        # split owner/repo if needed
        tmp = df["full_name"].astype(str).str.split("/", n=1, expand=True)
        if "owner" not in df.columns: df["owner"] = tmp[0]
        if "repo" not in df.columns: df["repo"] = tmp[1]
    if "owner" not in df.columns or "repo" not in df.columns:
        raise SystemExit("Input must have columns 'owner' and 'repo' (or a 'full_name' to split).")

    df["owner"] = df["owner"].astype(str).str.strip()
    df["repo"]  = df["repo"].astype(str).str.strip()
    df["full_name"] = df["owner"] + "/" + df["repo"]

    # Choose stratification columns if present
    group_cols = []
    for c in ["license_family", "language"]:
        if c in df.columns:
            group_cols.append(c)

    sample = stratified_sample(df, args.n, group_cols)
    sample = sample.reset_index(drop=True)

    sess = make_session(token)

    records = []
    counters = {
        "total": 0, "ok": 0, "network_error": 0, "http_error": 0,
        "http_404": 0, "http_403": 0, "other_http": 0
    }

    for idx, row in sample.iterrows():
        full_name = row["full_name"]
        owner = row["owner"]; repo = row["repo"]
        input_lang  = row.get("language", None)
        input_family = row.get("license_family", None)
        input_spdx = row.get("spdx", None)
        input_stars = row.get("stars", None)

        counters["total"] += 1
        repo_js, err = fetch_repo(sess, full_name)

        api_status = "ok"
        api_spdx = api_license_name = api_license_key = None
        api_family = "Unknown"
        api_stars = api_archived = api_disabled = None
        api_created = api_updated = api_pushed = None
        api_default_branch = api_latest_sha = None
        api_html_url = None

        if err == "network_error" or repo_js is None:
            counters["network_error"] += 1
            api_status = "network_error"
        elif isinstance(repo_js, dict) and repo_js.get("status_code"):
            sc = repo_js.get("status_code")
            counters["http_error"] += 1
            if sc == 404: counters["http_404"] += 1
            elif sc == 403: counters["http_403"] += 1
            else: counters["other_http"] += 1
            api_status = f"http_{sc}"
        else:
            counters["ok"] += 1
            lic = repo_js.get("license")
            if lic:
                api_spdx = lic.get("spdx_id")
                api_license_name = lic.get("name")
                api_license_key = lic.get("key")
            api_family = spdx_to_family(api_spdx)
            api_stars = repo_js.get("stargazers_count")
            api_archived = bool(repo_js.get("archived"))
            api_disabled = bool(repo_js.get("disabled"))
            api_created = repo_js.get("created_at")
            api_updated = repo_js.get("updated_at")
            api_pushed  = repo_js.get("pushed_at")
            api_default_branch = repo_js.get("default_branch")
            api_html_url = repo_js.get("html_url")

            # Try to get a snapshot SHA of the default branch head
            if api_default_branch:
                sha = fetch_latest_commit_sha(sess, owner, repo, api_default_branch)
                api_latest_sha = sha

        rec = {
            "owner": owner,
            "repo": repo,
            "full_name": full_name,
            "input_language": input_lang,
            "input_license_family": input_family,
            "input_spdx": input_spdx,
            "input_stars": input_stars,
            "api_status": api_status,
            "api_html_url": api_html_url,
            "api_license_spdx": api_spdx,
            "api_license_name": api_license_name,
            "api_license_key": api_license_key,
            "api_license_family": api_family,
            "api_stars": api_stars,
            "api_archived": api_archived,
            "api_disabled": api_disabled,
            "api_created_at": api_created,
            "api_updated_at": api_updated,
            "api_pushed_at": api_pushed,
            "api_default_branch": api_default_branch,
            "api_latest_commit_sha": api_latest_sha,
        }
        records.append(rec)

        # Friendly, low-key pacing to avoid spikes (especially on Windows)
        if counters["total"] % 50 == 0:
            time.sleep(1)

    out_df = pd.DataFrame.from_records(records)
    out_df.to_csv(args.out, index=False, encoding="utf-8")

    # Build a compact summary JSON
    def safe_val(x): return "Unknown" if pd.isna(x) or x in (None, "", "NONE", "NOASSERTION") else str(x)

    # Confusion matrix: input family vs API family
    cm = {}
    if "input_license_family" in out_df.columns:
        for _, r in out_df.iterrows():
            i = safe_val(r.get("input_license_family"))
            a = safe_val(r.get("api_license_family"))
            cm.setdefault(i, {}).setdefault(a, 0)
            cm[i][a] += 1

    family_counts = out_df["api_license_family"].fillna("Unknown").value_counts().to_dict()

    summary = {
        "sampled_total": int(counters["total"]),
        "api_ok": int(counters["ok"]),
        "api_errors": {
            "network_error": int(counters["network_error"]),
            "http_error_total": int(counters["http_error"]),
            "http_404": int(counters["http_404"]),
            "http_403": int(counters["http_403"]),
            "http_other": int(counters["other_http"]),
        },
        "api_license_family_counts": family_counts,
        "confusion_matrix_input_vs_api_family": cm,
        "notes": [
            "api_license_* comes from GitHub REST v3 /repos/{owner}/{repo}.",
            "api_latest_commit_sha is the head of default branch at verification time.",
            "License family computed via SPDX → family heuristic inside this script."
        ]
    }

    with open(args.summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Wrote CSV: {args.out}")
    print(f"Wrote JSON: {args.summary}")

if __name__ == "__main__":
    main()
