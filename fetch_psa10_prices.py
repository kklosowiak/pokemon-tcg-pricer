import os
import re
import time
import random
import urllib.parse
import pandas as pd
import requests
from bs4 import BeautifulSoup

CSV_PATH = "C:/Users/konra/Downloads/export-with-pricecharting.csv"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_card_name(name):
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
    return name.strip()

def clean_price(price_str):
    if not price_str or price_str == '-':
        return None
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
    
    if norm_card_num not in norm_title and norm_card_num not in norm_url:
        return -1
        
    score = 0
    
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
                
    clean_name = clean_card_name(target_card['Product Name']).lower()
    words = clean_name.split()
    matched_words = sum(1 for w in words if w in title_lower)
    score += matched_words
    
    return score

def parse_prices(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    prices = {}
    
    full_prices_section = soup.find('div', id='full-prices')
    if full_prices_section:
        table = full_prices_section.find('table')
        if table:
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 2:
                    prices[tds[0].text.strip()] = tds[1].text.strip()
                    
    if not prices:
        price_data_table = soup.find('table', id='price_data')
        if price_data_table:
            for tr in price_data_table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 2:
                    prices[tds[0].text.strip()] = tds[1].text.strip()
                    
    return prices

def get_page_with_retry(url):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r
            elif r.status_code == 429:
                print(f"Rate limited (429) on {url}. Sleeping 15s...")
                time.sleep(15)
            else:
                print(f"Status code {r.status_code} for {url}. Sleeping 5s...")
                time.sleep(5)
        except Exception as e:
            print(f"Error requesting {url}: {e}. Sleeping 5s...")
            time.sleep(5)
    return None

def lookup_psa10(row):
    # If we already have a valid game URL, use it directly
    url = row.get('PC URL')
    if pd.notna(url) and '/game/' in str(url):
        print(f"Using saved URL: {url}")
        r = get_page_with_retry(str(url))
        if r:
            prices_dict = parse_prices(r.text)
            psa10 = clean_price(prices_dict.get('PSA 10') or prices_dict.get('Grade 10'))
            print(f"  PSA 10 Price: {psa10}")
            return str(url), psa10
            
    # Otherwise, perform standard search/resolve
    card_num = str(row['Card Number']).strip()
    card_name = str(row['Product Name']).strip()
    
    cleaned_name = clean_card_name(card_name)
    query = f"{card_num} {cleaned_name}"
    
    search_url = f"https://www.pricecharting.com/search-products?q={urllib.parse.quote(query)}&type=prices"
    print(f"Searching: {query}")
    
    r = get_page_with_retry(search_url)
    if not r:
        return None, None
        
    final_url = r.url
    if r.history or '/game/' in r.url:
        final_url = r.url.split('?')[0]
        prices_dict = parse_prices(r.text)
    else:
        soup = BeautifulSoup(r.text, 'html.parser')
        game_links = []
        for l in soup.find_all('a'):
            href = l.get('href')
            if href and '/game/' in href:
                title = l.text.strip() or href.split('/')[-1].replace('-', ' ')
                game_links.append((title, href))
                
        if not game_links:
            return None, None
            
        scored_links = []
        for title, href in game_links:
            full_url = href if href.startswith('http') else f"https://www.pricecharting.com{href}"
            score = score_match(title, full_url, row)
            if score >= 0:
                scored_links.append((score, title, full_url))
                
        if not scored_links:
            return None, None
            
        scored_links.sort(key=lambda x: x[0], reverse=True)
        best_score, best_title, best_url = scored_links[0]
        print(f"  Matched: {best_title} (score={best_score})")
        
        time.sleep(random.uniform(0.3, 0.6))
        r_var = get_page_with_retry(best_url)
        if not r_var:
            return best_url, None
            
        final_url = best_url
        prices_dict = parse_prices(r_var.text)
        
    psa10 = clean_price(prices_dict.get('PSA 10') or prices_dict.get('Grade 10'))
    print(f"  PSA 10 Price: {psa10}")
    return final_url, psa10

def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH)
    
    if 'PC Grade 10' not in df.columns:
        df['PC Grade 10'] = None
        
    print(f"Loaded {len(df)} cards. Fetching PSA 10 prices...")
    
    count_updated = 0
    for idx, row in df.iterrows():
        psa10_val = row.get('PC Grade 10')
        
        # Only fetch if missing
        if pd.notna(psa10_val) and str(psa10_val).strip() != '':
            continue
            
        print(f"\n[{idx + 1}/{len(df)}] {row['Product Name']} ({row['Card Number']})...")
        
        final_url, psa10 = lookup_psa10(row)
        
        df.at[idx, 'PC URL'] = final_url
        df.at[idx, 'PC Grade 10'] = psa10
        
        count_updated += 1
        
        if count_updated % 5 == 0:
            print("Saving progress to CSV...")
            df.to_csv(CSV_PATH, index=False)
            
        # Politeness sleep: sleep 0.6 to 1.2 seconds between cards to avoid rate limit
        time.sleep(random.uniform(0.6, 1.2))
        
    print("Saving final results...")
    df.to_csv(CSV_PATH, index=False)
    print("Done!")

if __name__ == "__main__":
    main()
