import pandas as pd

CSV_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"

def main():
    df = pd.read_csv(CSV_PATH)
    
    # Ensure numeric columns are cleaned and numeric
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce').fillna(1)
    df['TCGplayer Raw Price'] = pd.to_numeric(df['TCGplayer Raw Price'], errors='coerce').fillna(0)
    
    # 1. Total for TCGplayer raw price (unmodified)
    df['Total Raw'] = df['TCGplayer Raw Price'] * df['Quantity']
    total_raw_val = df['Total Raw'].sum()
    
    # 2. Total with tiered discounts:
    # 80% on cards $20 or more
    # 60% on cards less than $20
    def calc_tiered_price(row):
        price = row['TCGplayer Raw Price']
        qty = row['Quantity']
        if price >= 20.0:
            return (price * 0.80) * qty
        else:
            return (price * 0.60) * qty
            
    df['Total Tiered'] = df.apply(calc_tiered_price, axis=1)
    total_tiered_val = df['Total Tiered'].sum()
    
    print(f"Total TCGplayer Raw Value: ${total_raw_val:,.2f}")
    print(f"Total Valued Price (80% for >=$20, 60% for <$20): ${total_tiered_val:,.2f}")
    
    # Count of cards in each tier
    cards_geq_20 = df[df['TCGplayer Raw Price'] >= 20.0]
    cards_lt_20 = df[df['TCGplayer Raw Price'] < 20.0]
    print(f"\nBreakdown:")
    print(f"- Cards >= $20 (Valued at 80%): {int(cards_geq_20['Quantity'].sum())} copies of {len(cards_geq_20)} distinct cards")
    print(f"- Cards < $20 (Valued at 60%): {int(cards_lt_20['Quantity'].sum())} copies of {len(cards_lt_20)} distinct cards")

if __name__ == "__main__":
    main()
