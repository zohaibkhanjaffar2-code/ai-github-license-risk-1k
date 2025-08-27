# GitHub License Risk Snapshot (n=1000)

**What this is:** We checked 1,000 GitHub repositories and read their license info directly from the GitHub API.
**Why it matters:** Generative AI platforms should know which repos are generally safe to include in training sets (permissive), which require share-alike planning (copyleft / weak-copyleft), and which are high-risk (unknown).

## Headline Results
- Permissive: 569
- Unknown: 303
- Copyleft: 93
- Weak-copyleft: 25
- Public-domain: 5
- Other: 5

![Verified License Families](api_family_bar.png)

## How we verified
- Called GitHub REST v3 `/repos/{owner}/{repo}` for each repo to get the SPDX and license name.
- Normalized to families: Permissive, Weak-copyleft, Copyleft, Public-domain, Other, Unknown.
- Snapshotted the default-branch commit SHA at verification time.

## What platforms should do
- **Include (Permissive):** keep an attribution log and preserve license texts/notices.
- **Handle with care (Weak/Copyleft):** only include if you're prepared for share-alike obligations on distribution of code/model artifacts.
- **Exclude by default (Unknown):** no clear permission -- resolve or skip.

*Generated 2025-08-27 21:51*
