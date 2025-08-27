# -*- coding: utf-8 -*-
import pandas as pd, json, datetime as dt, pathlib

df = pd.read_csv("verified_1k.csv")
with open("verified_1k_summary.json","r",encoding="utf-8") as f:
    summary = json.load(f)

n = len(df)
fam_counts = summary.get("api_license_family_counts", {})
lines = [f"- {k}: {v}" for k,v in sorted(fam_counts.items(), key=lambda kv: kv[1], reverse=True)]

report = f"""# GitHub License Risk Snapshot (n={n})

**What this is:** We checked 1,000 GitHub repositories and read their license info directly from the GitHub API.
**Why it matters:** Generative AI platforms should know which repos are generally safe to include in training sets (permissive), which require share-alike planning (copyleft / weak-copyleft), and which are high-risk (unknown).

## Headline Results
{chr(10).join(lines)}

![Verified License Families](api_family_bar.png)

## How we verified
- Called GitHub REST v3 `/repos/{{owner}}/{{repo}}` for each repo to get the SPDX and license name.
- Normalized to families: Permissive, Weak-copyleft, Copyleft, Public-domain, Other, Unknown.
- Snapshotted the default-branch commit SHA at verification time.

## What platforms should do
- **Include (Permissive):** keep an attribution log and preserve license texts/notices.
- **Handle with care (Weak/Copyleft):** only include if you're prepared for share-alike obligations on distribution of code/model artifacts.
- **Exclude by default (Unknown):** no clear permission -- resolve or skip.

*Generated {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
pathlib.Path("REPORT.md").write_text(report, encoding="utf-8")
