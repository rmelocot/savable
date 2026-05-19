import json
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Generic terms and city/region names that aren't useful as place names
SKIP_NAMES = {
    "samme", "lyng", "pal", "canada", "ontario",
    "toronto", "mississauga", "niagara falls",
    "brampton", "vaughan", "scarborough", "markham",
    "explore", "travel", "world", "fyp",
}

# Social media handles are lowercase alphanumeric strings with no spaces
_HANDLE_RE = re.compile(r'^[a-z0-9._]+$')

def looks_like_handle(name: str) -> bool:
    return bool(_HANDLE_RE.match(name.strip()))

def looks_like_ocr_garbage(name: str) -> bool:
    # Very short strings are unlikely to be meaningful place names
    if len(name) < 4:
        return True
    # Real place names almost always contain at least one vowel
    if not re.search(r'[aeiouAEIOU]', name):
        return True
    # Multiple short all-caps tokens are a strong sign of garbled OCR text
    all_caps_words = [w for w in name.split() if w.isupper() and len(w) <= 4]
    if len(all_caps_words) >= 2:
        return True
    return False

def run():
    with open(os.path.join(BASE_DIR, "data/extracted_places.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_results = []

    for item in data:
        # Prefer the enriched place name from extraction; fall back to the top candidate
        clean_name = item.get("enriched_place_name") or (item["place_names"][0] if item.get("place_names") else None)

        if clean_name:
            # Strip leading @ signs that may have carried over from social handles
            if clean_name.startswith("@"):
                clean_name = clean_name[1:].strip()
            # Discard names that are too generic, look like account handles, or appear to be OCR noise
            if clean_name.lower().strip() in SKIP_NAMES:
                clean_name = None
            elif looks_like_handle(clean_name):
                clean_name = None
            elif looks_like_ocr_garbage(clean_name):
                clean_name = None

        # Prefer the enriched address; fall back to the first raw address found during extraction
        clean_address = item.get("enriched_address") or (item["addresses"][0] if item.get("addresses") else None)

        cleaned_results.append({
            "tiktok_id":     item.get("tiktok_id"),
            "tiktok_url":    item.get("tiktok_url"),
            "name":          clean_name,
            "address":       clean_address,
            "latitude":      item.get("latitude"),
            "longitude":     item.get("longitude"),
            "category":      item.get("category"),
            "original_text": item.get("original_text"),
            "transcript":    item.get("transcript"),
            "thumbnail":     item.get("thumbnail"),
        })

    with open(os.path.join(BASE_DIR, "data/cleaned_places.json"), "w", encoding="utf-8") as f:
        json.dump(cleaned_results, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(cleaned_results)} cleaned places.")


if __name__ == "__main__":
    run()