import pandas as pd

df = pd.read_csv("pokemon_comps.csv")

total_sticker = df['sticker'].sum()
total_raw = df['raw'].sum()
total_psa_8 = df['psa_8'].sum()
total_psa_9 = df['psa_9'].sum()
total_psa_10 = df['psa_10'].sum()

print(f"Total Cards: {len(df)}")
print(f"Total Sticker Value: ${total_sticker:,.2f}")
print(f"Total PriceCharting Raw: ${total_raw:,.2f}")
print(f"Total PSA 8 Graded Value: ${total_psa_8:,.2f}")
print(f"Total PSA 9 Graded Value: ${total_psa_9:,.2f}")
print(f"Total PSA 10 Graded Value: ${total_psa_10:,.2f}")
