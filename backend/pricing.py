import requests
from bs4 import BeautifulSoup
import time
import random
import re
import urllib.parse
from config import JUSTTCG_API_KEY, POLITENESS_DELAY

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_price(price_str):
    if not price_str or price_str == '-':
        return None
    cleaned = price_str.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

def make_pc_url(name, set_name, num):
    # Normalize name: lower case, replace spaces with hyphens, keep ampersand
    name_clean = name.lower().replace(" ", "-").replace("&", "and").replace("'", "%27")
    set_clean = set_name.lower().replace(" ", "-")
    return f"https://www.pricecharting.com/game/pokemon-{set_clean}/{name_clean}-{num}"

def parse_price_data(soup):
    prices = {}
    table = soup.find('table', id='price_data')
    if not table:
        table = soup.find('table', class_='info_box')
    if table:
        rows = table.find_all('tr')
        if len(rows) >= 2:
            headers_list = [td.text.strip() for td in rows[0].find_all(['td', 'th'])]
            values_list = [td.text.strip() for td in rows[1].find_all(['td', 'th'])]
            for h, v in zip(headers_list, values_list):
                if h:
                    val_lines = [line.strip() for line in v.split('\n') if line.strip()]
                    val = val_lines[0] if val_lines else None
                    prices[h] = clean_price(val)
    return prices

def get_pricecharting_comps(name, set_name, num):
    url = make_pc_url(name, set_name, num)
    retries = 3
    backoff = 15
    
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                final_url = r.url
                if "/search-products" in final_url:
                    return {"raw": None, "psa_8": None, "psa_9": None, "psa_10": None, "url": final_url, "note": "Redirected to search"}
                
                soup = BeautifulSoup(r.text, 'html.parser')
                prices = parse_price_data(soup)
                
                raw = prices.get('Ungraded') or prices.get('Loose')
                psa_8 = prices.get('Grade 8') or prices.get('Graded')
                psa_9 = prices.get('Grade 9')
                psa_10 = prices.get('PSA 10') or prices.get('Grade 10')
                
                return {
                    "raw": raw,
                    "psa_8": psa_8,
                    "psa_9": psa_9,
                    "psa_10": psa_10,
                    "url": final_url,
                    "note": "Success"
                }
            elif r.status_code == 429:
                time.sleep(backoff)
                backoff *= 2
            else:
                time.sleep(3)
        except Exception as e:
            time.sleep(3)
            
    return {"raw": None, "psa_8": None, "psa_9": None, "psa_10": None, "url": url, "note": "Failed after retries"}

def get_tcgplayer_price(name, set_name, num):
    if not JUSTTCG_API_KEY:
        return None
        
    query = f"{name}"
    search_url = f"https://api.justtcg.com/v1/cards?q={urllib.parse.quote(query)}"
    
    headers_api = {
        'x-api-key': JUSTTCG_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        r = requests.get(search_url, headers=headers_api, timeout=10)
        if r.status_code == 200:
            data = r.json()
            cards_list = data.get("data", [])
            
            # Simple scoring/matching to find the correct set and card number
            best_match = None
            best_score = -1
            
            for card in cards_list:
                card_name = str(card.get("name", "")).lower()
                card_set = str(card.get("set", "")).lower()
                card_number = str(card.get("number", "")).lower()
                
                # Check name similarity
                if name.lower() not in card_name:
                    continue
                    
                score = 0
                
                # Check set match
                # E.g. set_name = "ruby-&-sapphire", card_set = "ex ruby & sapphire"
                norm_target_set = set_name.lower().replace("-", " ").replace("ex ", "").replace("ex-", "")
                norm_card_set = card_set.replace("-", " ").replace("ex ", "").replace("ex-", "")
                
                # Jaccard overlap of words
                target_words = set(norm_target_set.split())
                card_words = set(norm_card_set.split())
                if target_words.intersection(card_words):
                    score += 5
                
                # Check number match
                # E.g. target num = "98", card_number = "98/109" or "98"
                clean_target_num = num.strip().lstrip("0")
                clean_card_num = card_number.split("/")[0].strip().lstrip("0")
                if clean_target_num == clean_card_num:
                    score += 10
                elif clean_target_num in card_number:
                    score += 5
                    
                if score > best_score:
                    best_score = score
                    best_match = card
            
            if best_match and best_score >= 10: # must match card number
                variants = best_match.get("variants", [])
                # Try to find Near Mint
                for v in variants:
                    cond = str(v.get("condition", "")).lower()
                    if "near mint" in cond:
                        return v.get("price")
                # Fallback to first variant
                if variants:
                    return variants[0].get("price")
                    
    except Exception as e:
        pass
        
    return None
