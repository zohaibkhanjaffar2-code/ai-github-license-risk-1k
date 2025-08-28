import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path
here=Path(__file__).resolve().parent
df = pd.read_csv(here/'verified_122k.csv')
ok = df[df["api_status"]=="200"]

fam = ok["api_license_family"].fillna("Unknown")
spdx = ok["api_license_spdx"].fillna("")

plt.figure()
fam.value_counts().sort_values(ascending=False).plot(kind="bar")
plt.title("Verified License Families (HTTP 200) — 122k")
plt.xlabel("Family"); plt.ylabel("Count"); plt.tight_layout()
plt.savefig(here/'api_family_bar_122k.png', dpi=150)

plt.figure()
fam.value_counts().plot(kind="pie", autopct="%1.1f%%")
plt.title("Verified License Families (HTTP 200) — 122k")
plt.ylabel(""); plt.tight_layout()
plt.savefig(here/'api_family_pie_122k.png', dpi=150)

plt.figure()
spdx.value_counts().head(12).plot(kind="bar")
plt.title("Top SPDX (HTTP 200) — 122k")
plt.xlabel("SPDX"); plt.ylabel("Count"); plt.tight_layout()
plt.savefig(here/'top_spdx_bar_122k.png', dpi=150)
