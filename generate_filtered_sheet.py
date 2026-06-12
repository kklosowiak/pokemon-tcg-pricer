import os
import pandas as pd

CSV_INPUT_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"
TSV_OUTPUT_PATH = "C:/Users/konra/Downloads/export-for-sheets.txt"
CSV_OUTPUT_PATH = "C:/Users/konra/Downloads/export-with-pricecharting-filtered.csv"

def main():
    if not os.path.exists(CSV_INPUT_PATH):
        print(f"CSV not found at {CSV_INPUT_PATH}")
        return
        
    df = pd.read_csv(CSV_INPUT_PATH)
    
    # Ensure numeric columns are cleaned and numeric
    df['PC Ungraded (Raw)'] = pd.to_numeric(df['PC Ungraded (Raw)'], errors='coerce')
    df['TCGplayer Raw Price'] = pd.to_numeric(df['TCGplayer Raw Price'], errors='coerce')
    df['PC Grade 8'] = pd.to_numeric(df['PC Grade 8'], errors='coerce')
    df['PC Grade 9'] = pd.to_numeric(df['PC Grade 9'], errors='coerce')
    df['PC Grade 10'] = pd.to_numeric(df['PC Grade 10'], errors='coerce')
    
    # Recalculate Avg Ungraded, Spreads, and Profits
    df['Avg Ungraded'] = df[['PC Ungraded (Raw)', 'TCGplayer Raw Price']].mean(axis=1)
    df['PSA 10 Profit'] = df['PC Grade 10'] - df['Avg Ungraded'] - 30
    df['PSA 9 Net'] = df['PC Grade 9'] - df['Avg Ungraded'] - 30
    df['PSA 8 Net'] = df['PC Grade 8'] - df['Avg Ungraded'] - 30
    
    # Apply Filters:
    # 1. PriceCharting Ungraded (Raw) <= 50
    mask_pc_raw_50 = df['PC Ungraded (Raw)'] <= 50.0
    
    # 2. PSA 10 Profit (after $30 fee) > 150
    mask_profit_150 = df['PSA 10 Profit'] > 150.0
    
    # 3. PSA 8 Net >= -10 OR PSA 9 Net >= -10 (close to break even)
    mask_break_even = (df['PSA 8 Net'] >= -10.0) | (df['PSA 9 Net'] >= -10.0)
    
    filtered_df = df[mask_pc_raw_50 & mask_profit_150 & mask_break_even].copy()
    
    # Sort by PSA 10 Profit descending
    filtered_df = filtered_df.sort_values(by='PSA 10 Profit', ascending=False)
    
    print(f"Filtered down to {len(filtered_df)} cards matching all criteria.")
    
    # Save as TSV for sheets
    filtered_df.to_csv(TSV_OUTPUT_PATH, sep='\t', index=False)
    print(f"Saved TSV for copy-pasting to {TSV_OUTPUT_PATH}")
    
    # Save as CSV
    filtered_df.to_csv(CSV_OUTPUT_PATH, index=False)
    print(f"Saved CSV to {CSV_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
