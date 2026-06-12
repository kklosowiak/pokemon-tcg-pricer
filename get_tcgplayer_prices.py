import os
import re
import urllib.parse
import json
import time
import random
import pandas as pd
import requests

CSV_INPUT_PATH = "C:/Users/konra/Downloads/export-with-pricecharting.csv"
CSV_OUTPUT_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-final.csv"
API_KEY = "tcg_8de0be839c274f1a857254c6497d0f55"

def clean_card_name(name):
    # Remove trailing parentheticals
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
    return name.strip()

def match_variant(variants, target_condition, target_variance):
    target_cond_lower = str(target_condition).lower().strip()
    target_var_lower = str(target_variance).lower().strip()
    
    # Try exact match first
    for v in variants:
        v_cond = str(v.get('condition', '')).lower().strip()
        v_print = str(v.get('printing', '')).lower().strip()
        
        # Match condition
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
            
        # Match printing
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
            
    # Fallback to condition-only match if printing is not found
    for v in variants:
        v_cond = str(v.get('condition', '')).lower().strip()
        if target_cond_lower in v_cond or v_cond in target_cond_lower:
            return v
            
    # Fallback to any variant if nothing matches
    if variants:
        return variants[0]
        
    return None

def main():
    if not os.path.exists(CSV_INPUT_PATH):
        print(f"CSV not found at {CSV_INPUT_PATH}")
        return
        
    df = pd.read_csv(CSV_INPUT_PATH)
    print(f"Loaded CSV with {len(df)} rows.")
    
    # 1. Fetch YGOPRODeck database to get TCGplayer IDs
    print("Fetching YGOPRODeck database for TCGplayer Product IDs...")
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
                    
    print(f"Built mapping for {len(set_to_id)} set codes.")
    
    # Map tcgplayer IDs in dataframe
    df['tcgplayer_id'] = df['Card Number'].apply(lambda x: set_to_id.get(str(x).lower().strip()))
    
    # Filter for unique valid TCGplayer IDs
    unique_ids = df['tcgplayer_id'].dropna().unique().tolist()
    print(f"Found {len(unique_ids)} unique TCGplayer Product IDs to look up.")
    
    # 2. Batch request JustTCG API in chunks of 20 (limit for Free tier is 20)
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    all_cards_data = {}
    chunk_size = 20
    
    print("Querying JustTCG API in batches of 20...")
    for idx in range(0, len(unique_ids), chunk_size):
        chunk = unique_ids[idx:idx+chunk_size]
        body = [{'tcgplayerId': cid} for cid in chunk]
        
        try:
            r = requests.post("https://api.justtcg.com/v1/cards", headers=headers, json=body, timeout=20)
            if r.status_code == 200:
                res_data = r.json().get('data', [])
                for card in res_data:
                    tid = str(card.get('tcgplayerId'))
                    all_cards_data[tid] = card.get('variants', [])
                print(f"  Successfully fetched batch {idx//chunk_size + 1}/{len(unique_ids)//chunk_size + 1} ({len(res_data)} cards).")
            else:
                print(f"  Failed batch {idx//chunk_size + 1} with status {r.status_code}: {r.text}")
        except Exception as e:
            print(f"  Error on batch {idx//chunk_size + 1}: {e}")
            
        time.sleep(random.uniform(0.3, 0.6)) # rate limit politeness
            
    print(f"Retrieved variants for {len(all_cards_data)} cards from JustTCG API.")
    
    # 3. Match variants and populate the new column
    df['TCGplayer Raw Price'] = None
    
    matched_count = 0
    missing_count = 0
    for idx, row in df.iterrows():
        tid = str(row['tcgplayer_id']) if pd.notna(row['tcgplayer_id']) else None
        if not tid or tid not in all_cards_data:
            missing_count += 1
            continue
            
        variants = all_cards_data[tid]
        condition = row['Card Condition']
        variance = row['Variance']
        
        matched_v = match_variant(variants, condition, variance)
        if matched_v:
            price = matched_v.get('price')
            df.at[idx, 'TCGplayer Raw Price'] = price
            matched_count += 1
        else:
            missing_count += 1
            
    print(f"Successfully matched TCGplayer price for {matched_count} rows. Missing/no price for {missing_count} rows.")
    
    # Drop temp column
    df = df.drop(columns=['tcgplayer_id'])
    
    # Save back to local workspace
    df.to_csv(CSV_OUTPUT_PATH, index=False)
    print(f"Saved changes to local workspace at {CSV_OUTPUT_PATH}")

if __name__ == "__main__":
    main()
