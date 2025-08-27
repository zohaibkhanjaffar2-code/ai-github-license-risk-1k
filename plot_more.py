import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('verified_1k.csv')
fam = df['api_license_family'].fillna('Unknown')
spdx = df['api_license_spdx'].fillna('')

# Pie of families
plt.figure()
fam.value_counts().plot(kind='pie', autopct='%1.1f%%')
plt.title('Verified License Families (n=1000)')
plt.ylabel('')
plt.tight_layout()
plt.savefig('api_family_pie.png', dpi=150)

# Top 10 SPDX IDs
top = spdx.value_counts().head(10)
plt.figure()
top.plot(kind='bar')
plt.title('Top 10 SPDX Identifiers (Verified)')
plt.xlabel('SPDX')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('top_spdx_bar.png', dpi=150)
