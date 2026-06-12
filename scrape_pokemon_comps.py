import requests
from bs4 import BeautifulSoup
import time
import random
import csv
import sys
import os

# Configure stdout to use utf-8
sys.stdout.reconfigure(encoding='utf-8')

cards = [
    {"id": 1, "name": "Shiftry ex", "set": "power-keepers", "num": "97", "sticker": 50},
    {"id": 2, "name": "Claydol ex", "set": "legend-maker", "num": "93", "sticker": 70},
    {"id": 3, "name": "Medicham ex", "set": "emerald", "num": "95", "sticker": 80},
    {"id": 4, "name": "Mightyena ex", "set": "holon-phantoms", "num": "101", "sticker": 80},
    {"id": 5, "name": "Hitmonchan ex", "set": "ruby-&-sapphire", "num": "98", "sticker": 80},
    {"id": 6, "name": "Delcatty ex", "set": "crystal-guardians", "num": "91", "sticker": 80},
    {"id": 7, "name": "Shiftry ex", "set": "crystal-guardians", "num": "97", "sticker": 80},
    {"id": 8, "name": "Aggron ex", "set": "sandstorm", "num": "95", "sticker": 80},
    {"id": 9, "name": "Sneasel ex", "set": "ruby-&-sapphire", "num": "103", "sticker": 85},
    {"id": 10, "name": "Muk ex", "set": "dragon", "num": "96", "sticker": 100},
    {"id": 11, "name": "Wailord ex", "set": "sandstorm", "num": "100", "sticker": 130},
    {"id": 12, "name": "Regirock ex", "set": "hidden-legends", "num": "98", "sticker": 150},
    {"id": 13, "name": "Rayquaza ex", "set": "dragon", "num": "97", "sticker": 150},
    {"id": 14, "name": "Flygon ex", "set": "legend-maker", "num": "87", "sticker": 180},
    {"id": 15, "name": "Arcanine ex", "set": "legend-maker", "num": "83", "sticker": 500},
    {"id": 16, "name": "Salamence ex", "set": "deoxys", "num": "103", "sticker": 250},
    {"id": 17, "name": "Steelix ex", "set": "unseen-forces", "num": "109", "sticker": 250},
    {"id": 18, "name": "Vaporeon ex", "set": "delta-species", "num": "110", "sticker": 300},
    {"id": 19, "name": "Swampert ex", "set": "crystal-guardians", "num": "98", "sticker": 300},
    {"id": 20, "name": "Zapdos ex", "set": "fire-red-&-leaf-green", "num": "116", "sticker": 150},
    {"id": 21, "name": "Moltres ex", "set": "fire-red-&-leaf-green", "num": "115", "sticker": 200},
    {"id": 22, "name": "Articuno ex", "set": "fire-red-&-leaf-green", "num": "114", "sticker": 250},
    {"id": 23, "name": "Clefable ex", "set": "fire-red-&-leaf-green", "num": "106", "sticker": 100},
    {"id": 24, "name": "Aggron ex", "set": "crystal-guardians", "num": "89", "sticker": 140},
    {"id": 25, "name": "Dustox ex", "set": "legend-maker", "num": "86", "sticker": 70},
    {"id": 26, "name": "Rocket's Hitmonchan ex", "set": "team-rocket-returns", "num": "98", "sticker": 400},
    {"id": 27, "name": "Tyranitar ex", "set": "dragon-frontiers", "num": "99", "sticker": 350}
]

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

def make_url(name, set_name, num):
    # Keep apostrophe as %27, replace spaces with hyphens, keep ampersand
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

def get_page_with_retry(url):
    retries = 5
    backoff = 20
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r
            elif r.status_code == 429:
                print(f"  [429 Rate Limited] Attempt {attempt+1}/{retries}. Sleeping {backoff}s...", flush=True)
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"  [Status {r.status_code}] Attempt {attempt+1}/{retries}. Sleeping 5s...", flush=True)
                time.sleep(5)
        except Exception as e:
            print(f"  [Exception: {e}] Attempt {attempt+1}/{retries}. Sleeping 5s...", flush=True)
            time.sleep(5)
    return None

results = []

print("Starting Scraper...", flush=True)
for i, c in enumerate(cards):
    url = make_url(c["name"], c["set"], c["num"])
    print(f"[{i+1}/{len(cards)}] Scraping {c['name']} ({c['set']} #{c['num']})...", flush=True)
    print(f"  URL: {url}", flush=True)
    
    r = get_page_with_retry(url)
    if not r:
        print(f"  [FAILED] Could not load page.", flush=True)
        results.append({
            "id": c["id"], "name": c["name"], "set": c["set"], "num": c["num"], "sticker": c["sticker"],
            "raw": None, "psa_8": None, "psa_9": None, "psa_10": None, "url": url, "note": "Failed to load page"
        })
        time.sleep(1)
        continue
        
    final_url = r.url
    is_search = "/search-products" in final_url
    if is_search:
        print(f"  [WARNING] Redirected to search: {final_url}", flush=True)
        results.append({
            "id": c["id"], "name": c["name"], "set": c["set"], "num": c["num"], "sticker": c["sticker"],
            "raw": None, "psa_8": None, "psa_9": None, "psa_10": None, "url": final_url, "note": "Redirected to search"
        })
    else:
        soup = BeautifulSoup(r.text, 'html.parser')
        prices = parse_price_data(soup)
        
        # Extract desired prices
        raw = prices.get('Ungraded') or prices.get('Loose')
        psa_8 = prices.get('Grade 8') or prices.get('Graded')
        psa_9 = prices.get('Grade 9')
        psa_10 = prices.get('PSA 10') or prices.get('Grade 10')
        
        print(f"  [OK] Raw: {raw}, PSA 8: {psa_8}, PSA 9: {psa_9}, PSA 10: {psa_10}", flush=True)
        results.append({
            "id": c["id"], "name": c["name"], "set": c["set"], "num": c["num"], "sticker": c["sticker"],
            "raw": raw, "psa_8": psa_8, "psa_9": psa_9, "psa_10": psa_10, "url": final_url, "note": "Success"
        })
        
    time.sleep(random.uniform(1.2, 2.2))

# Save results to CSV
csv_file = "pokemon_comps.csv"
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["id", "name", "set", "num", "sticker", "raw", "psa_8", "psa_9", "psa_10", "url", "note"])
    writer.writeheader()
    writer.writerows(results)

print(f"\nSaved results to {csv_file}", flush=True)

# Generate clipboard-ready output (TSV format)
print("\n=== CLIPBOARD READY TSV START ===", flush=True)
# Headers
print("ID\tName\tSet\tCard #\tSticker Price\tPriceCharting Raw\tPSA 8 Price\tPSA 9 Price\tPSA 10 Price\tPriceCharting URL", flush=True)
for r in results:
    raw_str = f"${r['raw']:.2f}" if r['raw'] is not None else ""
    psa_8_str = f"${r['psa_8']:.2f}" if r['psa_8'] is not None else ""
    psa_9_str = f"${r['psa_9']:.2f}" if r['psa_9'] is not None else ""
    psa_10_str = f"${r['psa_10']:.2f}" if r['psa_10'] is not None else ""
    sticker_str = f"${r['sticker']:.2f}"
    
    print(f"{r['id']}\t{r['name']}\t{r['set']}\t{r['num']}\t{sticker_str}\t{raw_str}\t{psa_8_str}\t{psa_9_str}\t{psa_10_str}\t{r['url']}", flush=True)
print("=== CLIPBOARD READY TSV END ===", flush=True)
