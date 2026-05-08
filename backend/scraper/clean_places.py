import json

# LOAD EXTRACTED DATA
with open("backend/data/extracted_places.json", "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned_results = []

for item in data:

    # =========================
    # CLEAN NAME
    # =========================
    clean_name = None

    if item.get("enriched_place_name"):

        clean_name = item["enriched_place_name"]

    elif item.get("place_names"):

        if len(item["place_names"]) > 0:
            clean_name = item["place_names"][0]

    # =========================
    # CLEAN ADDRESS
    # =========================
    clean_address = None

    if item.get("enriched_address"):
        clean_address = item["enriched_address"]

    elif item.get("addresses"):

        if len(item["addresses"]) > 0:
            clean_address = item["addresses"][0]

    # =========================
    # FINAL CLEAN OBJECT
    # =========================
    cleaned_item = {

        "tiktok_id": item.get("tiktok_id"),

        "tiktok_url": item.get("tiktok_url"),

        "name": clean_name,

        "address": clean_address,

        "latitude": item.get("latitude"),

        "longitude": item.get("longitude"),

        "category": item.get("category"),

        "original_text": item.get("original_text")
    }

    cleaned_results.append(cleaned_item)

# SAVE CLEAN DATA
with open("backend/data/cleaned_places.json", "w", encoding="utf-8") as f:

    json.dump(
        cleaned_results,
        f,
        indent=4,
        ensure_ascii=False
    )

print("Saved", len(cleaned_results), "cleaned places.")