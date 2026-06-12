import os
import re
import time
import random
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup

CSV_PATH = "C:/Users/konra/Documents/antigravity/vibrant-brahmagupta/export-with-pricecharting.csv"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_card_name(name):
    # Remove trailing parentheticals
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
    return name.strip()

def clean_price(price_str):
    if not price_str or price_str == '-':
        return None
    # Remove $, commas, whitespace
    cleaned = price_str.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def score_match(link_title, link_url, target_card):
    title_lower = link_title.lower()
    url_lower = link_url.lower()
    
    card_num = str(target_card.get('Card Number', '')).lower().strip()
    if not card_num:
        return -1
        
    norm_card_num = card_num.replace('-', '').replace(' ', '')
    norm_title = title_lower.replace('-', '').replace(' ', '')
    norm_url = url_lower.replace('-', '').replace(' ', '').replace('_', '')
    
    # Card number must be in the title or the URL
    if norm_card_num not in norm_title and norm_card_num not in norm_url:
        return -1
        
    score = 0
    
    # Check Variance (Edition)
    variance = str(target_card.get('Variance', '')).lower()
    is_1st_target = '1st' in variance or 'first' in variance
    is_limited_target = 'limited' in variance or 'ltd' in variance
    
    is_1st_title = '1st' in title_lower or 'first' in title_lower
    is_limited_title = 'limited' in title_lower or 'ltd' in title_lower
    
    if is_1st_target == is_1st_title:
        score += 2
    else:
        score -= 2
        
    if is_limited_target == is_limited_title:
        score += 2
    else:
        score -= 2
        
    # Check Rarity keywords
    rarity = str(target_card.get('Rarity', '')).lower()
    rarities = ['ultimate', 'secret', 'ghost', 'starlight', 'quarter century', 'collector', 'pharaoh']
    for r in rarities:
        has_r_target = r in rarity
        has_r_title = r in title_lower
        if has_r_target == has_r_title:
            score += 1
        else:
            if has_r_target:
                score -= 3
                
    # Check name match similarity
    clean_name = clean_card_name(target_card['Product Name']).lower()
    words = clean_name.split()
    matched_words = sum(1 for w in words if w in title_lower)
    score += matched_words
    
    return score

def parse_prices(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    prices = {}
    
    # Try div id="full-prices" table first
    full_prices_section = soup.find('div', id='full-prices')
    if full_prices_section:
        table = full_prices_section.find('table')
        if table:
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 2:
                    prices[tds[0].text.strip()] = tds[1].text.strip()
                    
    # Fallback to #price_data table
    if not prices:
        price_data_table = soup.find('table', id='price_data')
        if price_data_table:
            for tr in price_data_table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 2:
                    prices[tds[0].text.strip()] = tds[1].text.strip()
                    
    return prices

def get_page_with_retry(url):
    for attempt in range(2):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r
            elif r.status_code == 429:
                print(f"Rate limited (429) on {url}. Waiting 15s...")
                time.sleep(15)
            else:
                print(f"Non-200 status code {r.status_code} for {url}. Waiting 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"Error requesting {url}: {e}. Waiting 5s...")
            time.sleep(5)
    return None

def lookup_card_price(row):
    card_num = str(row['Card Number']).strip()
    card_name = str(row['Product Name']).strip()
    
    if not card_num or not card_name:
        return None, None, None, None, "Invalid card name/number"
        
    cleaned_name = clean_card_name(card_name)
    query = f"{card_num} {cleaned_name}"
    
    search_url = f"https://www.pricecharting.com/search-products?q={urllib.parse.quote(query)}&type=prices"
    print(f"Searching: {query}")
    
    r = get_page_with_retry(search_url)
    if not r:
        return None, None, None, None, "Request failed"
        
    # Check if we redirected directly to a game page
    if r.history or '/game/' in r.url:
        final_url = r.url.split('?')[0] # strip query params
        prices_dict = parse_prices(r.text)
    else:
        # Search page, parse links
        soup = BeautifulSoup(r.text, 'html.parser')
        game_links = []
        for l in soup.find_all('a'):
            href = l.get('href')
            if href and '/game/' in href:
                title = l.text.strip() or href.split('/')[-1].replace('-', ' ')
                game_links.append((title, href))
                
        if not game_links:
            return None, None, None, None, "No search results"
            
        # Score links to find best match
        scored_links = []
        for title, href in game_links:
            # Complete the URL if relative
            full_url = href if href.startswith('http') else f"https://www.pricecharting.com{href}"
            score = score_match(title, full_url, row)
            if score >= 0:
                scored_links.append((score, title, full_url))
                
        if not scored_links:
            return None, None, None, None, "No matching variants in search"
            
        # Pick the highest scoring link
        scored_links.sort(key=lambda x: x[0], reverse=True)
        best_score, best_title, best_url = scored_links[0]
        print(f"  Picked variant: {best_title} (score={best_score})")
        
        # Request the variant page
        time.sleep(random.uniform(0.3, 0.7))
        r_var = get_page_with_retry(best_url)
        if not r_var:
            return None, None, None, best_url, "Variant request failed"
            
        final_url = best_url
        prices_dict = parse_prices(r_var.text)
        
    # Extract Ungraded, Grade 8, Grade 9
    ungraded = clean_price(prices_dict.get('Ungraded') or prices_dict.get('Loose'))
    grade_8 = clean_price(prices_dict.get('Grade 8') or prices_dict.get('Graded')) # Graded is sometimes general graded price
    grade_9 = clean_price(prices_dict.get('Grade 9'))
    
    # Log found prices
    print(f"  Found prices -> Raw: {ungraded}, PSA 8: {grade_8}, PSA 9: {grade_9}")
    return final_url, ungraded, grade_8, grade_9, None

def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH)
    
    # Make sure we have the required columns
    cols_to_add = ['PC URL', 'PC Ungraded (Raw)', 'PC Grade 8', 'PC Grade 9', 'PC Note']
    for col in cols_to_add:
        if col not in df.columns:
            df[col] = None
            
    print(f"Loaded {len(df)} cards. Checking for missing prices...")
    
    count_updated = 0
    for idx, row in df.iterrows():
        # Check if already filled
        url_val = row.get('PC URL')
        ungraded_val = row.get('PC Ungraded (Raw)')
        
        # If both URL and Ungraded are present, skip
        if pd.notna(url_val) and str(url_val).strip() != '' and pd.notna(ungraded_val):
            continue
            
        print(f"\n[{idx + 1}/{len(df)}] Looking up {row['Product Name']} ({row['Card Number']})...")
        
        final_url, ungraded, grade_8, grade_9, note = lookup_card_price(row)
        
        df.at[idx, 'PC URL'] = final_url
        df.at[idx, 'PC Ungraded (Raw)'] = ungraded
        df.at[idx, 'PC Grade 8'] = grade_8
        df.at[idx, 'PC Grade 9'] = grade_9
        df.at[idx, 'PC Note'] = note
        
        count_updated += 1
        
        # Save every 5 updates
        if count_updated % 5 == 0:
            print("Saving progress...")
            df.to_csv(CSV_PATH, index=False)
            
        # Politeness sleep
        time.sleep(random.uniform(0.5, 1.2))
        
    print("Saving final results...")
    df.to_csv(CSV_PATH, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
