import requests
import json

headers = {"x-api-key": "tcg_8de0be839c274f1a857254c6497d0f55"}
url = "https://api.justtcg.com/v1/cards?q=Blue-Eyes+White+Dragon"

r = requests.get(url, headers=headers)
data = r.json()
print("Keys in root:", data.keys())
print("Number of cards:", len(data.get("data", [])))
if len(data.get("data", [])) > 0:
    card = data["data"][0]
    print("Keys in a card:", card.keys())
    print("Card example (excluding variants):", {k: v for k, v in card.items() if k != "variants"})
    if "variants" in card and len(card["variants"]) > 0:
        print("Keys in variant:", card["variants"][0].keys())
        print("Variant example:", card["variants"][0])
