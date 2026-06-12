import requests
import time
import random

cards = [
    {"name": "Shiftry ex", "set": "sandstorm", "num": "97", "sticker": 50},
    {"name": "Claydol ex", "set": "legend-maker", "num": "93", "sticker": 70},
    {"name": "Medicham ex", "set": "emerald", "num": "95", "sticker": 80},
    {"name": "Mightyena ex", "set": "holon-phantoms", "num": "101", "sticker": 80},
    {"name": "Hitmonchan ex", "set": "ruby-&-sapphire", "num": "98", "sticker": 80},
    {"name": "Delcatty ex", "set": "ruby-&-sapphire", "num": "91", "sticker": 80},
    {"name": "Shiftry ex", "set": "crystal-guardians", "num": "97", "sticker": 80},
    {"name": "Aggron ex", "set": "sandstorm", "num": "95", "sticker": 80},
    {"name": "Sneasel ex", "set": "ruby-&-sapphire", "num": "103", "sticker": 85},
    {"name": "Muk ex", "set": "dragon", "num": "96", "sticker": 100},
    {"name": "Wailord ex", "set": "sandstorm", "num": "100", "sticker": 130},
    {"name": "Regirock ex", "set": "hidden-legends", "num": "98", "sticker": 150},
    {"name": "Rayquaza ex", "set": "dragon", "num": "97", "sticker": 150},
    {"name": "Flygon ex", "set": "legend-maker", "num": "92", "sticker": 180},
    {"name": "Arcanine ex", "set": "legend-maker", "num": "83", "sticker": 500},
    {"name": "Salamence ex", "set": "deoxys", "num": "103", "sticker": 250},
    {"name": "Steelix ex", "set": "unseen-forces", "num": "109", "sticker": 250},
    {"name": "Vaporeon ex", "set": "delta-species", "num": "110", "sticker": 300},
    {"name": "Swampert ex", "set": "crystal-guardians", "num": "98", "sticker": 300},
    {"name": "Zapdos ex", "set": "firered-&-leafgreen", "num": "116", "sticker": 150},
    {"name": "Moltres ex", "set": "firered-&-leafgreen", "num": "115", "sticker": 200},
    {"name": "Articuno ex", "set": "firered-&-leafgreen", "num": "114", "sticker": 250},
    {"name": "Clefable ex", "set": "firered-&-leafgreen", "num": "106", "sticker": 100},
    {"name": "Aggron ex", "set": "crystal-guardians", "num": "89", "sticker": 140},
    {"name": "Dustox ex", "set": "legend-maker", "num": "86", "sticker": 70},
    {"name": "Rocket's Hitmonchan ex", "set": "team-rocket-returns", "num": "99", "sticker": 400},
    {"name": "Tyranitar ex", "set": "dragon-frontiers", "num": "99", "sticker": 350}
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def make_url(name, set_name, num):
    # Normalize name: lower case, replace spaces with hyphens, remove special characters (like apostrophes)
    name_clean = name.lower().replace(" ", "-").replace("'", "").replace("&", "and")
    # Clean the set name slug
    set_clean = set_name.lower().replace(" ", "-").replace("&", "and")
    return f"https://www.pricecharting.com/game/pokemon-{set_clean}/{name_clean}-{num}"

print("Checking URLs...")
failures = []
for i, c in enumerate(cards):
    url = make_url(c["name"], c["set"], c["num"])
    print(f"[{i+1}/{len(cards)}] Checking: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            failures.append((c["name"], c["set"], c["num"], url, r.status_code))
            print(f"  [FAILED] Status code: {r.status_code}")
        else:
            print(f"  [OK]")
    except Exception as e:
        failures.append((c["name"], c["set"], c["num"], url, f"Exception: {e}"))
        print(f"  [FAILED] Exception: {e}")
    time.sleep(random.uniform(0.5, 1.2))

if failures:
    print(f"\nFailed {len(failures)} URLs:")
    for name, set_name, num, url, status in failures:
        print(f"- {name} ({set_name} #{num}) status {status}: {url}")
else:
    print("\nAll URLs matched successfully!")
