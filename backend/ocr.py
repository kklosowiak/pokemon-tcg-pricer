import google.generativeai as genai
import json
from config import GEMINI_API_KEY

def perform_ocr(image_bytes: bytes, mime_type: str):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set the GEMINI_API_KEY variable in your Render settings.")
    
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Use gemini-1.5-flash for fast and inexpensive vision processing
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Analyze the uploaded image which contains one or more Pokémon cards.
    Identify all cards present in the image. For each card, extract:
    1. Card Name (e.g. 'Charizard ex', 'Rayquaza ex', "Rocket's Hitmonchan ex")
    2. Set Name - normalize the set name to the official English set name, e.g. 'FireRed & LeafGreen', 'Dragon Frontiers', 'Legend Maker', 'Emerald', 'Power Keepers', 'Ruby & Sapphire', 'Crystal Guardians', 'Sandstorm', 'Dragon', 'Hidden Legends', 'Deoxys', 'Unseen Forces', 'Delta Species', 'Team Rocket Returns', 'Holon Phantoms'.
    3. Card Number - the card number printed on the bottom right (e.g., '97', '103', '98'). Only output the number, not the set size (e.g. if it says 98/109, only extract '98').
    
    Format the response as a valid JSON array of objects with the keys:
    "name", "set", "number".
    
    Example output format:
    [
      {"name": "Shiftry ex", "set": "Power Keepers", "number": "97"},
      {"name": "Claydol ex", "set": "Legend Maker", "number": "93"}
    ]
    
    Return ONLY the raw JSON array, without any markdown formatting block (like ```json ... ```).
    """
    
    image_part = {
        "mime_type": mime_type,
        "data": image_bytes
    }
    
    response = model.generate_content([image_part, prompt])
    text = response.text.strip()
    
    # Strip markdown code blocks if the model accidentally included them
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
        
    text = text.strip()
    
    # Parse to validate JSON
    parsed_json = json.loads(text)
    return parsed_json
