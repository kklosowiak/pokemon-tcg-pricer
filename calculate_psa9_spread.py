import os
import pandas as pd

CSV_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"

def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH)
    
    # Ensure numeric columns are cleaned and numeric
    df['PC Ungraded (Raw)'] = pd.to_numeric(df['PC Ungraded (Raw)'], errors='coerce')
    df['TCGplayer Raw Price'] = pd.to_numeric(df['TCGplayer Raw Price'], errors='coerce')
    df['PC Grade 9'] = pd.to_numeric(df['PC Grade 9'], errors='coerce')
    
    # Avg Ungraded
    df['Avg Ungraded'] = df[['PC Ungraded (Raw)', 'TCGplayer Raw Price']].mean(axis=1)
    
    # PSA 9 Spread
    df['PSA 9 Spread'] = df['PC Grade 9'] - df['Avg Ungraded']
    
    # Filter for cards over $30
    mask_over_30 = (df['PC Ungraded (Raw)'] > 30) | (df['TCGplayer Raw Price'] > 30)
    over_30_df = df[mask_over_30].copy()
    
    # Sort by the PSA 9 Spread descending
    over_30_df_sorted = over_30_df.sort_values(by='PSA 9 Spread', ascending=False)
    
    print(f"Found {len(over_30_df)} cards over $30.")
    print("\nTop 15 cards by PSA 9 Spread (PSA 9 Price - Avg Ungraded):")
    for idx, r in over_30_df_sorted.head(15).iterrows():
        name = r['Product Name']
        set_code = r['Card Number']
        pc_raw = r['PC Ungraded (Raw)']
        tcg_raw = r['TCGplayer Raw Price']
        avg_raw = r['Avg Ungraded']
        psa9 = r['PC Grade 9']
        spread = r['PSA 9 Spread']
        print(f"- {name} ({set_code}):")
        print(f"  TCGplayer: ${tcg_raw:,.2f} | PC Raw: ${pc_raw:,.2f} | Avg Raw: ${avg_raw:,.2f}")
        print(f"  PSA 9: ${psa9:,.2f} | Spread: ${spread:,.2f}")
        
    # Save the updated CSV
    df.to_csv(CSV_PATH, index=False)

if __name__ == "__main__":
    main()
