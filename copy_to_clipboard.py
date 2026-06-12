import pandas as pd
import subprocess
import sys

# Configure stdout to use utf-8
sys.stdout.reconfigure(encoding='utf-8')

csv_path = "pokemon_comps.csv"
df = pd.read_csv(csv_path)

# Build TSV text
tsv_lines = []
# Headers
headers = ["ID", "Name", "Set", "Card #", "Sticker Price", "PriceCharting Raw", "PSA 8 Price", "PSA 9 Price", "PSA 10 Price", "PriceCharting URL"]
tsv_lines.append("\t".join(headers))

for idx, row in df.iterrows():
    raw_str = f"${row['raw']:.2f}" if pd.notna(row['raw']) else ""
    psa_8_str = f"${row['psa_8']:.2f}" if pd.notna(row['psa_8']) else ""
    psa_9_str = f"${row['psa_9']:.2f}" if pd.notna(row['psa_9']) else ""
    psa_10_str = f"${row['psa_10']:.2f}" if pd.notna(row['psa_10']) else ""
    sticker_str = f"${row['sticker']:.2f}"
    
    line = [
        str(row['id']),
        str(row['name']),
        str(row['set']),
        str(row['num']),
        sticker_str,
        raw_str,
        psa_8_str,
        psa_9_str,
        psa_10_str,
        str(row['url'])
    ]
    tsv_lines.append("\t".join(line))

tsv_content = "\r\n".join(tsv_lines) # Windows line endings

# Write to tsv file
with open("pokemon_comps.tsv", "w", encoding="utf-8") as f:
    f.write(tsv_content)

print("Writing TSV to clipboard via clip.exe...")
try:
    process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
    process.communicate(input=tsv_content)
    print("Successfully copied to clipboard!")
except Exception as e:
    print(f"Error copying to clipboard: {e}")
