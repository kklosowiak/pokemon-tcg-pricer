import pandas as pd

CSV_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"

def main():
    df = pd.read_csv(CSV_PATH)
    
    df['PC Ungraded (Raw)'] = pd.to_numeric(df['PC Ungraded (Raw)'], errors='coerce')
    df['TCGplayer Raw Price'] = pd.to_numeric(df['TCGplayer Raw Price'], errors='coerce')
    df['PC Grade 8'] = pd.to_numeric(df['PC Grade 8'], errors='coerce')
    df['PC Grade 9'] = pd.to_numeric(df['PC Grade 9'], errors='coerce')
    df['PC Grade 10'] = pd.to_numeric(df['PC Grade 10'], errors='coerce')
    
    df['Avg Ungraded'] = df[['PC Ungraded (Raw)', 'TCGplayer Raw Price']].mean(axis=1)
    df['PSA 10 Profit'] = df['PC Grade 10'] - df['Avg Ungraded'] - 30
    df['PSA 9 Net'] = df['PC Grade 9'] - df['Avg Ungraded'] - 30
    df['PSA 8 Net'] = df['PC Grade 8'] - df['Avg Ungraded'] - 30
    
    mask_under_50 = df['Avg Ungraded'] < 50.0
    mask_profit_150 = df['PSA 10 Profit'] > 150.0
    mask_break_even = (df['PSA 8 Net'] >= -10.0) | (df['PSA 9 Net'] >= -10.0)
    
    candidates = df[mask_under_50 & mask_profit_150 & mask_break_even].copy()
    candidates_sorted = candidates.sort_values(by='PSA 10 Profit', ascending=False)
    
    print("TOTAL MATCHING CANDIDATES:", len(candidates_sorted))
    print("\nTop 20 candidates:")
    for idx, r in candidates_sorted.head(20).iterrows():
        print(f"- {r['Product Name']} ({r['Card Number']}):")
        print(f"  Avg Raw: ${r['Avg Ungraded']:.2f} | PSA 10 Price: ${r['PC Grade 10']:.2f} | PSA 10 Profit: +${r['PSA 10 Profit']:.2f}")
        print(f"  PSA 9 Price: ${r['PC Grade 9']:.2f} (Net: {r['PSA 9 Net']:+.2f})")
        print(f"  PSA 8 Price: ${r['PC Grade 8']:.2f} (Net: {r['PSA 8 Net']:+.2f})")

if __name__ == "__main__":
    main()
