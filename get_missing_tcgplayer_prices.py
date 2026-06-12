import os
import re
import urllib.parse
import json
import time
import random
import pandas as pd
import requests

CSV_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"
API_KEY = "tcg_8de0be839c274f1a857254c6497d0f55"

def clean_card_name(name):
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
    return name.strip()

def match_variant(variants, target_condition, target_variance):
    target_cond_lower = str(target_condition).lower().strip()
    target_var_lower = str(target_variance).lower().strip()
    
    for v in variants:
        v_cond = str(v.get('condition', '')).lower().strip()
        v_print = str(v.get('printing', '')).lower().strip()
        
        cond_match = False
        if target_cond_lower == v_cond:
            cond_match = True
        elif 'near mint' in target_cond_lower and 'near mint' in v_cond:
            cond_match = True
        elif 'lightly played' in target_cond_lower and 'lightly played' in v_cond:
            cond_match = True
        elif 'moderately played' in target_cond_lower and 'moderately played' in v_cond:
            cond_match = True
        elif 'heavily played' in target_cond_lower and 'heavily played' in v_cond:
            cond_match = True
        elif 'damaged' in target_cond_lower and 'damaged' in v_cond:
            cond_match = True
            
        print_match = False
        if target_var_lower == v_print:
            print_match = True
        elif '1st' in target_var_lower and '1st' in v_print:
            print_match = True
        elif 'unlimited' in target_var_lower and 'unlimited' in v_print:
            print_match = True
        elif 'limited' in target_var_lower and 'limited' in v_print:
            print_match = True
        elif v_print == 'normal' or not v_print:
            print_match = True
            
        if cond_match and print_match:
            return v
            
    for v in variants:
        v_cond = str(v.get('condition', '')).lower().strip()
        if target_cond_lower in v_cond or v_cond in target_cond_lower:
            return v
            
    if variants:
        return variants[0]
        
    return None

def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded CSV with {len(df)} rows.")
    
    # Check what is missing
    # Since we need to look up missing ones, we map tcgplayer_id again
    print("Fetching YGOPRODeck database for set-code-to-ID mapping...")
    db_r = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?tcgplayer_data=yes").json()
    
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
                    
    df['tcgplayer_id'] = df['Card Number'].apply(lambda x: set_to_id.get(str(x).lower().strip()))
    
    # We find rows where 'TCGplayer Raw Price' is null/NaN
    missing_mask = df['TCGplayer Raw Price'].isna()
    missing_df = df[missing_mask]
    
    unique_missing_ids = missing_df['tcgplayer_id'].dropna().unique().tolist()
    print(f"Total rows missing TCGplayer price: {len(missing_df)}")
    print(f"Unique TCGplayer Product IDs to look up: {len(unique_missing_ids)}")
    
    if len(unique_missing_ids) == 0:
        print("No missing TCGplayer prices to fetch!")
        df = df.drop(columns=['tcgplayer_id'])
        df.to_csv(CSV_PATH, index=False)
        return
        
    # Query in batches of 20, but sleep 6.5 seconds between requests
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    all_cards_data = {}
    chunk_size = 20
    
    print("Querying missing cards from JustTCG API in batches of 20 with 6.5s delay...")
    for idx in range(0, len(unique_missing_ids), chunk_size):
        chunk = unique_missing_ids[idx:idx+chunk_size]
        body = [{'tcgplayerId': cid} for cid in chunk]
        
        # Sleep to avoid rate limits
        if idx > 0:
            print("  Sleeping 6.5 seconds...")
            time.sleep(6.5)
            
        for attempt in range(3):
            try:
                r = requests.post("https://api.justtcg.com/v1/cards", headers=headers, json=body, timeout=20)
                if r.status_code == 200:
                    res_data = r.json().get('data', [])
                    for card in res_data:
                        tid = str(card.get('tcgplayerId'))
                        all_cards_data[tid] = card.get('variants', [])
                    print(f"  Successfully fetched batch {idx//chunk_size + 1}/{len(unique_missing_ids)//chunk_size + 1} ({len(res_data)} cards).")
                    break
                elif r.status_code == 429:
                    print(f"  Rate limited (429) on batch {idx//chunk_size + 1}. Sleeping 20s...")
                    time.sleep(20)
                else:
                    print(f"  Status code {r.status_code} on batch {idx//chunk_size + 1}. Retrying in 10s...")
                    time.sleep(10)
            except Exception as e:
                print(f"  Error on batch {idx//chunk_size + 1}: {e}. Retrying in 10s...")
                time.sleep(10)
                
    print(f"Retrieved variants for {len(all_cards_data)} cards from JustTCG API.")
    
    # Match variants and populate missing rows
    matched_count = 0
    for idx, row in df.iterrows():
        if pd.notna(row['TCGplayer Raw Price']):
            continue
            
        tid = str(row['tcgplayer_id']) if pd.notna(row['tcgplayer_id']) else None
        if not tid or tid not in all_cards_data:
            continue
            
        variants = all_cards_data[tid]
        condition = row['Card Condition']
        variance = row['Variance']
        
        matched_v = match_variant(variants, condition, variance)
        if matched_v:
            price = matched_v.get('price')
            df.at[idx, 'TCGplayer Raw Price'] = price
            matched_count += 1
            
    print(f"Successfully matched TCGplayer price for {matched_count} missing rows.")
    
    # Drop temp column
    df = df.drop(columns=['tcgplayer_id'])
    
    # Save back to local workspace
    df.to_csv(CSV_PATH, index=False)
    print(f"Saved changes to local workspace at {CSV_PATH}")

if __name__ == "__main__":
    main()
