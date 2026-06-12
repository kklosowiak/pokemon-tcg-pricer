import pandas as pd

df = pd.read_csv("C:/Users/konra/Downloads/export-with-pricecharting.csv")

# Clean numeric fields
df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1)
df['PC Ungraded (Raw)'] = pd.to_numeric(df['PC Ungraded (Raw)'], errors='coerce')
df['PC Grade 8'] = pd.to_numeric(df['PC Grade 8'], errors='coerce')
df['PC Grade 9'] = pd.to_numeric(df['PC Grade 9'], errors='coerce')

# Calculate totals
total_qty = int(df['Quantity'].sum())
total_raw = (df['PC Ungraded (Raw)'].fillna(0) * df['Quantity']).sum()
total_psa8 = (df['PC Grade 8'].fillna(0) * df['Quantity']).sum()
total_psa9 = (df['PC Grade 9'].fillna(0) * df['Quantity']).sum()

print("Total Cards Count:", total_qty)
print(f"Total Raw (Ungraded) Value: ${total_raw:,.2f}")
print(f"Total PSA 8 Graded Value: ${total_psa8:,.2f}")
print(f"Total PSA 9 Graded Value: ${total_psa9:,.2f}")

# Top 5 most valuable raw cards
print("\nTop 5 Most Valuable Raw Cards:")
top_raw = df.sort_values(by='PC Ungraded (Raw)', ascending=False).head(5)
for _, r in top_raw.iterrows():
    print(f"- {r['Product Name']} ({r['Card Number']}): ${r['PC Ungraded (Raw)']:,.2f}")

# Top 5 most valuable PSA 9 cards
print("\nTop 5 Most Valuable PSA 9 Cards:")
top_psa9 = df.sort_values(by='PC Grade 9', ascending=False).head(5)
for _, r in top_psa9.iterrows():
    print(f"- {r['Product Name']} ({r['Card Number']}): ${r['PC Grade 9']:,.2f}")
