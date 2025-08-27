import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('verified_1k.csv')
counts = df['api_license_family'].fillna('Unknown').value_counts().sort_values(ascending=False)

plt.figure()
counts.plot(kind='bar')
plt.title('Verified License Families (n=1000)')
plt.xlabel('Family')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('api_family_bar.png', dpi=150)
