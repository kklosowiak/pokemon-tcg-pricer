import pandas as pd

CSV_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"

def main():
    df = pd.read_csv(CSV_PATH)
    
    df['PC Ungraded (Raw)'] = pd.to_numeric(df['PC Ungraded (Raw)'], errors='coerce')
    df['TCGplayer Raw Price'] = pd.to_numeric(df['TCGplayer Raw Price'], errors='coerce')
    df['PC Grade 8'] = pd.to_numeric(df['PC Grade 8'], errors='coerce')
    df['PC Grade 9'] = pd.to_numeric(df['PC Grade 9'], errors='coerce')
    
    df['Avg Ungraded'] = df[['PC Ungraded (Raw)', 'TCGplayer Raw Price']].mean(axis=1)
    df['PSA 8 Spread'] = df['PC Grade 8'] - df['Avg Ungraded']
    df['PSA 9 Spread'] = df['PC Grade 9'] - df['Avg Ungraded']
    
    psa8_candidates = df[df['PSA 8 Spread'] > 100].sort_values(by='PSA 8 Spread', ascending=False)
    psa9_candidates = df[df['PSA 9 Spread'] > 100].sort_values(by='PSA 9 Spread', ascending=False)
    
    print(f"=== PSA 8 Spread > $100 ({len(psa8_candidates)} Cards) ===")
    for _, r in psa8_candidates.iterrows():
        print(f"- {r['Product Name']} ({r['Card Number']}): Avg Raw: ${r['Avg Ungraded']:,.2f} | PSA 8: ${r['PC Grade 8']:,.2f} | Spread: +${r['PSA 8 Spread']:,.2f}")
        
    print(f"\n=== PSA 9 Spread > $100 ({len(psa9_candidates)} Cards) ===")
    for _, r in psa9_candidates.iterrows():
        print(f"- {r['Product Name']} ({r['Card Number']}): Avg Raw: ${r['Avg Ungraded']:,.2f} | PSA 9: ${r['PC Grade 9']:,.2f} | Spread: +${r['PSA 9 Spread']:,.2f}")

if __name__ == "__main__":
    main()
