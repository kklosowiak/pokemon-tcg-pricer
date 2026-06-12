import pandas as pd
import requests
import urllib.parse
import re

csv_path = "C:/Users/konra/Downloads/export-with-pricecharting.csv"
df = pd.read_csv(csv_path)

print("Fetching database...")
db_r = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?tcgplayer_data=yes").json()

# Build mapping
set_to_id = {}
for card in db_r.get("data", []):
    for card_set in card.get("card_sets", []):
        set_code = card_set.get("set_code")
        set_url = card_set.get("set_url")
        if set_code and set_url:
            decoded = urllib.parse.unquote(set_url)
            match = re.search(r'/product/(\d+)', decoded)
            if match:
                set_to_id[set_code.lower().strip()] = match.group(1)

print("Total mapped set codes in DB:", len(set_to_id))

# Test on our CSV
found = 0
missing = []
for idx, row in df.iterrows():
    card_num = str(row['Card Number']).lower().strip()
    if card_num in set_to_id:
        found += 1
    else:
        missing.append((row['Product Name'], row['Card Number']))

print(f"Matched {found} / {len(df)} cards")
print("Missing examples (first 10):", missing[:10])
