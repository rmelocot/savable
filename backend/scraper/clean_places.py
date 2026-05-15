import json
import re

with open("backend/data/extracted_places.json", "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned_results = []

# Names that are too generic or region-level to be useful as a display label.
SKIP_NAMES = {
    "samme", "lyng", "pal", "canada", "ontario",
    "toronto", "mississauga", "niagara falls",
}

for item in data:

    # Prefer the enriched name; fall back to the top candidate.
    clean_name = None

    if item.get("enriched_place_name"):
        clean_name = item["enriched_place_name"]
    elif item.get("place_names"):
        if len(item["place_names"]) > 0:
            clean_name = item["place_names"][0]

    # Strip leading @ that slipped through from artist/handle extraction.
    if clean_name and clean_name.startswith("@"):
        clean_name = clean_name[1:].strip()

    if clean_name and clean_name.lower().strip() in SKIP_NAMES:
        clean_name = None

    # Prefer the enriched address; fall back to the raw regex match.
    clean_address = None

    if item.get("enriched_address"):
        clean_address = item["enriched_address"]
    elif item.get("addresses"):
        if len(item["addresses"]) > 0:
            clean_address = item["addresses"][0]

    cleaned_item = {
        "tiktok_id":     item.get("tiktok_id"),
        "tiktok_url":    item.get("tiktok_url"),
        "name":          clean_name,
        "address":       clean_address,
        "latitude":      item.get("latitude"),
        "longitude":     item.get("longitude"),
        "category":      item.get("category"),
        "original_text": item.get("original_text"),
        "transcript":    item.get("transcript"),
    }

    cleaned_results.append(cleaned_item)

with open("backend/data/cleaned_places.json", "w", encoding="utf-8") as f:
    json.dump(cleaned_results, f, indent=4, ensure_ascii=False)

print(f"Saved {len(cleaned_results)} cleaned places.")