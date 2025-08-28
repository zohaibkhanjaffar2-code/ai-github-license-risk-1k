# GitHub License Risk — 122k Verification (Layman + Legal Guidance)

## Abstract
We verified license information for 122k GitHub repositories via the GitHub REST API and normalized licenses into families (Permissive, Weak-copyleft, Copyleft, Public-domain, Other, Unknown). We present headline ratios, top SPDX identifiers, and a data-informed legal exposure model for US/EU. This paper explains the results in plain language and gives concrete compliance steps for generative-AI platforms.

## How we did it (Method, in simple terms)
- Took a list of repos (owner/repo).
- Called GET /repos/{owner}/{repo} to read each repo’s declared license.
- Normalized SPDX strings into families.
- Counted results and saved a snapshot (with commit SHA optional).
- Plotted families and top SPDX IDs.

## Findings (HTTP 200 repos = 122720)
License families:
* Permissive: 70395 (57.36%)
* Unknown: 37057 (30.20%)
* Copyleft: 12155 (9.90%)
* Weak-copyleft: 2549 (2.08%)
* Public-domain: 323 (0.26%)
* Other: 241 (0.20%)

Top SPDX (first 12):
* MIT: 38611
* Apache-2.0: 27247
* : 25962
* NOASSERTION: 10697
* GPL-3.0: 8228
* BSD-3-Clause: 2491
* AGPL-3.0: 2084
* GPL-2.0: 1843
* BSD-2-Clause: 983
* MPL-2.0: 967
* LGPL-3.0: 913
* Unlicense: 487

## What this means (plain English)
- **Permissive** (e.g., MIT/Apache/BSD): generally safe to *include* in training sets if you keep attribution and preserve license texts.
- **Weak-copyleft / Copyleft** (e.g., LGPL/MPL vs GPL/AGPL/GPL): usable, but *only if* you plan for share-alike obligations when distributing covered code or certain model artifacts.
- **Unknown / NOASSERTION**: treat as **no permission** until clarified.

## Legal risk (data-informed; not legal advice)
- Fees usually dominate costs; see LEGAL_RISK_FORECAST.md for the current US/EU scenarios derived from the same snapshot.
- Jurisdiction matters (US: each side bears its own fees; EU: loser often pays part of the winner’s costs). Use venue-specific playbooks.

## Recommendations for GenAI Platforms
1) **Attribution ledger**: record repo URL, SPDX, author, and commit SHA for anything you ingest.
2) **Preserve license texts**: ship a license bundle/NOTICE file with your product and model cards.
3) **Gate on family**: allow Permissive by default; route Weak-/Copyleft through a legal checklist; block Unknown until resolved.
4) **Automated re-checks**: licenses can change; re-verify periodically.
5) **Honor removal requests**: document a process and service-level target.
6) **Publish policy**: be transparent about what you train on and why.

## Limitations & Next Steps
- We rely on GitHub’s declared license; some repos mis-declare or omit it.
- Training-time use vs distribution obligations can differ; edge cases require counsel review.
- Next: expand to more languages, add SHA pinning, and evaluate per-owner policy signals.

*(Generated from the 122k verification snapshot.)*
