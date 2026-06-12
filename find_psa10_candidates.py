import os
import pandas as pd

CSV_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"

def main():
    df = pd.read_csv(CSV_PATH)
    
    # Ensure numeric columns are cleaned and numeric
    df['PC Ungraded (Raw)'] = pd.to_numeric(df['PC Ungraded (Raw)'], errors='coerce')
    df['TCGplayer Raw Price'] = pd.to_numeric(df['TCGplayer Raw Price'], errors='coerce')
    df['PC Grade 8'] = pd.to_numeric(df['PC Grade 8'], errors='coerce')
    df['PC Grade 9'] = pd.to_numeric(df['PC Grade 9'], errors='coerce')
    df['PC Grade 10'] = pd.to_numeric(df['PC Grade 10'], errors='coerce')
    
    # Re-calculate Avg Ungraded (handles missing values)
    df['Avg Ungraded'] = df[['PC Ungraded (Raw)', 'TCGplayer Raw Price']].mean(axis=1)
    
    # Calculate spreads/nets
    # Cost = Avg Ungraded + $30 grading fee
    df['PSA 10 Profit'] = df['PC Grade 10'] - df['Avg Ungraded'] - 30
    df['PSA 9 Net'] = df['PC Grade 9'] - df['Avg Ungraded'] - 30
    df['PSA 8 Net'] = df['PC Grade 8'] - df['Avg Ungraded'] - 30
    
    # Filters:
    # 1. Worth less than $50 (Avg Ungraded < 50)
    # 2. Net over $150 profit if graded a PSA 10 (PSA 10 Profit > 150)
    # 3. Close to break even in PSA 8 or PSA 9 (PSA 8 Net >= -10 OR PSA 9 Net >= -10)
    
    mask_under_50 = df['Avg Ungraded'] < 50.0
    mask_profit_150 = df['PSA 10 Profit'] > 150.0
    mask_break_even = (df['PSA 8 Net'] >= -10.0) | (df['PSA 9 Net'] >= -10.0)
    
    candidates = df[mask_under_50 & mask_profit_150 & mask_break_even].copy()
    candidates_sorted = candidates.sort_values(by='PSA 10 Profit', ascending=False)
    
    print(f"Found {len(candidates_sorted)} grading candidates matching all criteria.")
    print("\nCandidates details:")
    for idx, r in candidates_sorted.iterrows():
        name = r['Product Name']
        set_code = r['Card Number']
        raw = r['Avg Ungraded']
        psa8_net = r['PSA 8 Net']
        psa9_net = r['PSA 9 Net']
        psa10_profit = r['PSA 10 Profit']
        psa10 = r['PC Grade 10']
        psa9 = r['PC Grade 9']
        psa8 = r['PC Grade 8']
        print(f"- {name} ({set_code}):")
        print(f"  Avg Raw: ${raw:,.2f} | PSA 10 Price: ${psa10:,.2f} | PSA 10 Profit: +${psa10_profit:,.2f}")
        print(f"  PSA 9 Price: ${psa9:,.2f} (Net: ${psa9_net:+,.2f})")
        print(f"  PSA 8 Price: ${psa8:,.2f} (Net: ${psa8_net:+,.2f})")
        
    # Save the updated CSV locally
    df.to_csv(CSV_PATH, index=False)
    print(f"\nSaved updated CSV with PSA 10 Spread / Profit columns to {CSV_PATH}")

if __name__ == "__main__":
    main()
