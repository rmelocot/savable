import json
import re
import os
import spacy
import cv2
import pytesseract
import yt_dlp
import tempfile
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

nlp = spacy.load("en_core_web_sm")

geolocator = Nominatim(user_agent="tiktok_place_extractor")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

address_pattern = re.compile(
    r'(?<!\d)'
    r'(?!(?:1[6-9]|20)\d\d\b)'
    r'\b\d{1,5}\s+'
    r'[A-Za-z]{2}[A-Za-z0-9\s,.-]*?'
    r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)'
    r'(?:\s+[NSEW])?'
    r'(?:\s+Unit\s+\w+)?'
    r'(?:,\s*[A-Za-z0-9\s-]+)*',
    re.IGNORECASE
)

CANADIAN_POSTAL_RE = re.compile(r'\b[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d\b')
FAKE_ADDRESS_BLACKLIST = {"1 free dr", "1 free drive"}

PLACE_ALIASES = {
    "cne":                          "Canadian National Exhibition, Toronto, Ontario",
    "canadian national exhibition": "Canadian National Exhibition, Toronto, Ontario",
    "eaton centre":                 "CF Eaton Centre, Toronto, Ontario",
    "eatoncentre":                  "CF Eaton Centre, Toronto, Ontario",
    "distillery district":          "Distillery District, Toronto, Ontario",
    "ripley's aquarium":            "Ripley's Aquarium of Canada, Toronto, Ontario",
    "cn tower":                     "CN Tower, Toronto, Ontario",
    "rogers centre":                "Rogers Centre, Toronto, Ontario",
    "scotiabank arena":             "Scotiabank Arena, Toronto, Ontario",
    "rainforest cafe":              "Rainforest Cafe, Niagara Falls, Ontario",
    "yorkdale":                     "Yorkdale Shopping Centre, Toronto, Ontario",
    "canada's wonderland":          "Canada's Wonderland, Vaughan, Ontario",
    "canadaswonderland":            "Canada's Wonderland, Vaughan, Ontario",
    "alpenfury":                    "Canada's Wonderland, Vaughan, Ontario",
    "alpen fury":                   "Canada's Wonderland, Vaughan, Ontario",
    "#alpenfury":                   "Canada's Wonderland, Vaughan, Ontario",
    "royal ontario museum":         "Royal Ontario Museum, Toronto, Ontario",
    "royalontariomuseum":           "Royal Ontario Museum, Toronto, Ontario",
    "romafterdark":                 "Royal Ontario Museum, Toronto, Ontario",
    "rom after dark":               "Royal Ontario Museum, Toronto, Ontario",
    "#romafterdark":                "Royal Ontario Museum, Toronto, Ontario",
    "edwardsgardens":               "Edwards Gardens, Toronto, Ontario",
    "edwardsgarden":                "Edwards Gardens, Toronto, Ontario",
    "edwardsgardentoronto":         "Edwards Gardens, Toronto, Ontario",
    "edwards gardens":              "Edwards Gardens, Toronto, Ontario",
    "edwards garden":               "Edwards Gardens, Toronto, Ontario",
}

ALIAS_DISPLAY_NAMES = {
    "Canadian National Exhibition, Toronto, Ontario":   "Canadian National Exhibition",
    "CF Eaton Centre, Toronto, Ontario":                "CF Eaton Centre",
    "Distillery District, Toronto, Ontario":            "Distillery District",
    "Ripley's Aquarium of Canada, Toronto, Ontario":    "Ripley's Aquarium of Canada",
    "CN Tower, Toronto, Ontario":                       "CN Tower",
    "Rogers Centre, Toronto, Ontario":                  "Rogers Centre",
    "Scotiabank Arena, Toronto, Ontario":               "Scotiabank Arena",
    "Rainforest Cafe, Niagara Falls, Ontario":          "Rainforest Cafe",
    "Yorkdale Shopping Centre, Toronto, Ontario":       "Yorkdale Shopping Centre",
    "Canada's Wonderland, Vaughan, Ontario":            "Canada's Wonderland",
    "Royal Ontario Museum, Toronto, Ontario":           "Royal Ontario Museum",
    "Edwards Gardens, Toronto, Ontario":                "Edwards Gardens",
}

ALIAS_FORCED_COORDS = {
    "Canada's Wonderland, Vaughan, Ontario": {
        "address":   "Canada's Wonderland, 1 Canada's Wonderland Drive, Vaughan, Ontario, L6A 1S6, Canada",
        "latitude":  43.8430,
        "longitude": -79.5390,
    },
    "Edwards Gardens, Toronto, Ontario": {
        "address":   "Edwards Gardens, 755 Lawrence Ave E, Toronto, Ontario, M3C 1P2, Canada",
        "latitude":  43.7310,
        "longitude": -79.3509,
    },
}

CONCERT_HASHTAGS_RE = re.compile(
    r'#(concert|tour|liveshow|liveevent|theromantictour)',
    re.IGNORECASE
)

CATEGORY_KEYWORDS = {
    "food": [
        "food", "restaurant", "buffet", "dessert", "cafe", "eat",
        "burger", "pizza", "ramen", "sushi", "brunch", "streetfood",
        "drink", "bbq", "coffee", "bakery", "night market",
    ],
    "shopping": [
        "mall", "shopping", "store", "plaza", "marketplace",
        "outlet", "boutique", "retail",
    ],
    "nature": [
        "park", "beach", "lake", "trail", "mountain", "hiking",
        "waterfall", "rainforest", "tree", "blossom", "tulip",
    ],
    "attractions": [
        "museum", "gallery", "landmark", "monument", "tourist",
        "attraction", "aquarium", "zoo", "observatory", "exhibit",
        "exhibition", "amusement", "wonderland", "amusementpark",
        "carnival", "cne", "underrated", "historical", "architecture",
        "heritage", "open doors", "treatment plant", "roller coaster",
        "theme park", "launchcoaster", "rollercoaster",
    ],
    "music": [
        "festival", "concert", "tour", "performance",
        "coachella", "lollapalooza", "osheaga", "live music",
    ],
}

BAD_PLACE_WORDS = {
    "google", "toronto", "canada", "ontario",
    "mississauga", "thailand", "bangkok",
    "always", "never", "live", "baby", "alway", "tesla",
}

HASHTAG_CITY_MAP = {
    "nashville":     "Nashville, Tennessee, USA",
    "newyork":       "New York City, New York, USA",
    "nyc":           "New York City, New York, USA",
    "losangeles":    "Los Angeles, California, USA",
    "la":            "Los Angeles, California, USA",
    "chicago":       "Chicago, Illinois, USA",
    "houston":       "Houston, Texas, USA",
    "miami":         "Miami, Florida, USA",
    "lasvegas":      "Las Vegas, Nevada, USA",
    "vancouver":     "Vancouver, British Columbia, Canada",
    "montreal":      "Montreal, Quebec, Canada",
    "calgary":       "Calgary, Alberta, Canada",
    "london":        "London, England, UK",
    "paris":         "Paris, France",
    "tokyo":         "Tokyo, Japan",
    "osaka":         "Osaka, Japan",
    "seoul":         "Seoul, South Korea",
    "bangkok":       "Bangkok, Thailand",
    "bali":          "Bali, Indonesia",
    "dubai":         "Dubai, UAE",
    "sydney":        "Sydney, New South Wales, Australia",
    "melbourne":     "Melbourne, Victoria, Australia",
    "rome":          "Rome, Italy",
    "barcelona":     "Barcelona, Spain",
    "amsterdam":     "Amsterdam, Netherlands",
    "berlin":        "Berlin, Germany",
    "atlanta":       "Atlanta, Georgia, USA",
    "pittsburgh":    "Pittsburgh, Pennsylvania, USA",
    "arizona":       "Phoenix, Arizona, USA",
    "hamilton":      "Hamilton, Ontario, Canada",
    "coachella":     "Indio, California, USA",
    "coachella2026": "Indio, California, USA",
}

CITY_FALLBACK_COORDS = {
    "Mississauga":   {"address": "Mississauga, Ontario, Canada",   "latitude": 43.5890, "longitude": -79.6441},
    "Brampton":      {"address": "Brampton, Ontario, Canada",      "latitude": 43.7315, "longitude": -79.7624},
    "Vaughan":       {"address": "Vaughan, Ontario, Canada",       "latitude": 43.8361, "longitude": -79.4983},
    "Toronto":       {"address": "Toronto, Ontario, Canada",       "latitude": 43.6532, "longitude": -79.3832},
    "Hamilton":      {"address": "Hamilton, Ontario, Canada",      "latitude": 43.2557, "longitude": -79.8711},
    "Niagara Falls": {"address": "Niagara Falls, Ontario, Canada", "latitude": 43.0962, "longitude": -79.0377},
}

NATURE_LANDMARK_RE = re.compile(
    r'\b(falls?|peak|gorge|ravine|gardens?|conservation\s+area|trail|beach|cove)\b',
    re.IGNORECASE
)

PLACE_NAME_OVERRIDES = {
    "rom":                "Royal Ontario Museum",
    "royalontariomuseum": "Royal Ontario Museum",
}


def detect_alias(text):
    text_lower = text.lower()
    for keyword, canonical in PLACE_ALIASES.items():
        if keyword in text_lower:
            return canonical
    return None


def geocode_result_is_specific(location) -> bool:
    if not location:
        return False
    raw_type  = location.raw.get("type", "")
    osm_class = location.raw.get("class", "")
    vague_types = {"administrative", "county", "region", "municipality", "city", "town", "village", "suburb"}
    if raw_type in vague_types:
        return False
    if osm_class in {"boundary", "place"} and raw_type in vague_types:
        return False
    return True


def strip_webvtt(text):
    text = re.sub(r'^WEBVTT\b.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[\.,]\d{3}[^\n]*', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def extract_video_text(url, num_frames=3, max_seconds=10):
    ocr_texts = []
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.mp4")
        ydl_opts = {
            "outtmpl":     video_path,
            "format":      "mp4/best[ext=mp4]/best",
            "quiet":       True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"  Video download failed: {e}")
            return ""

        if not os.path.exists(video_path):
            print("  Video file not found after download.")
            return ""

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        sample_until = min(duration, max_seconds)
        sample_frames = int(sample_until * fps)
        indices = (
            [int(i * sample_frames / (num_frames - 1)) for i in range(num_frames)]
            if num_frames > 1 else [0]
        )
        seen_texts = set()
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.dilate(thresh, kernel, iterations=1)
            raw = pytesseract.image_to_string(processed, config="--psm 6")
            cleaned = raw.strip()
            if cleaned and cleaned not in seen_texts:
                seen_texts.add(cleaned)
                ocr_texts.append(cleaned)
        cap.release()

    result = "\n".join(ocr_texts)
    print(f"  OCR extracted {len(ocr_texts)} unique frame(s) of text")
    return result


def ocr_has_canadian_postal(text: str) -> bool:
    return bool(CANADIAN_POSTAL_RE.search(text))


def is_real_address(addr: str) -> bool:
    if not addr:
        return False
    if addr.strip().lower() in FAKE_ADDRESS_BLACKLIST:
        return False
    if len(addr) > 120:
        return False
    if not re.search(r'\b(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b', addr, re.IGNORECASE):
        return False
    if not re.match(r'^\d', addr.strip()):
        return False
    if '\n' in addr:
        return False
    return True


def classify_post(text):
    if CONCERT_HASHTAGS_RE.search(text):
        return "music"
    text_lower = text.lower()
    scores = {cat: sum(1 for kw in kws if kw in text_lower) for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return "unknown" if scores[best] == 0 else best


def clean_candidate(text):
    text = text.strip()
    text = re.sub(r'[^\w\s&\'.,-]', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip(" -,|@.")


def is_valid_place(candidate):
    if not candidate:
        return False
    cl = candidate.lower()
    if len(candidate) < 3:
        return False
    if len(candidate.split()) > 6:
        return False
    if re.match(r'^[A-Z]{2}\s*[A-Z0-9]+$', candidate):
        return False
    if cl in BAD_PLACE_WORDS:
        return False
    bad_phrases = ["the place to be", "if youre", "along the way", "must visit", "picture-perfect"]
    return not any(p in cl for p in bad_phrases)


def extract_addresses(text):
    return [a for a in address_pattern.findall(text) if is_real_address(a)]

def extract_pin_emoji_place(text: str) -> str | None:
    pin_match = re.search(r'📍\s*([^\n]{3,80})', text)
    if not pin_match:
        return None
    raw = pin_match.group(1).split('\n')[0].strip()
    if raw and raw[0].islower():
        return None
    sentence_words = {"along", "the", "you", "will", "can", "this", "your", "our", "their"}
    first_word = raw.split()[0].lower() if raw.split() else ""
    if first_word in sentence_words:
        return None
    if len(raw) > 50:
        return None
    candidate = clean_candidate(raw)
    return candidate if is_valid_place(candidate) else None


def extract_place_candidates(text, score_boost=2):
    doc = nlp(text)
    local_scores = {}
    business_words = ["chicken", "cafe", "restaurant", "bbq", "burger", "pizza", "ramen", "sushi", "hot", "donut", "donuts", "birria", "taco", "tacos"]

    def add_local(candidate, score):
        if not is_valid_place(candidate):
            return
        for word in business_words:
            if word in candidate.lower():
                score += 3
        local_scores[candidate] = local_scores.get(candidate, 0) + score

    place_match = re.search(r'(?i)place:\s*([^:\n]+?)(?:location:|$)', text)
    if place_match:
        add_local(clean_candidate(place_match.group(1)), 5)

    pin_place = extract_pin_emoji_place(text)
    if pin_place:
        add_local(pin_place, 4)

    at_match = re.search(r'@\s*([A-Za-z0-9\s&\'.,-]{3,80})(?:\n|$)', text)
    if at_match:
        candidate = clean_candidate(at_match.group(1))
        if any(h in candidate.lower() for h in ["toronto", "mississauga", "brampton", "st", "ave", "road", "blvd", "bay", "king", "queen", "yonge"]):
            add_local(candidate, 5)

    for ent in doc.ents:
        if ent.label_ in ["FAC", "ORG", "LOC"]:
            add_local(clean_candidate(ent.text), score_boost)

    for pattern in [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Gardens|Cafe|Market|Park|Trail|Restaurant|Buffet|Mall|Waterfall|Centre|Center|Arena|Stadium|Gallery|Museum|Falls|Peak))',
        r'(?:at|visit|to)\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})',
    ]:
        for match in re.findall(pattern, text):
            add_local(clean_candidate(match), score_boost)

    for hashtag in re.findall(r'#([A-Za-z]{4,})', text):
        if len(hashtag) >= 6 and hashtag.lower() not in BAD_PLACE_WORDS:
            spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', hashtag)
            if spaced != hashtag:
                add_local(clean_candidate(spaced), 2)

    at_handle_in_text = re.search(r'@([A-Za-z0-9]{4,})', text)
    if at_handle_in_text:
        handle_lower = at_handle_in_text.group(1).lower()
        for hashtag in re.findall(r'#([A-Za-z]{4,})', text):
            if hashtag.lower() == handle_lower:
                add_local(hashtag.title(), 4)

    return local_scores


def extract_instagram_name(text: str) -> str | None:
    caption = text
    prefix_match = re.match(
        r'^\d[\d,KkMm\.]*\s+likes?,\s*\d[\d,KkMm\.]*\s+comments?\s*-\s*.+?\s+on\s+\w+\s+\d+,\s*\d{4}:\s*["\u201c]?',
        text,
        re.IGNORECASE
    )
    if prefix_match:
        caption = text[prefix_match.end():].lstrip('""\u201c').strip()

    pin_place = extract_pin_emoji_place(caption)
    if pin_place:
        print(f"  Instagram name (📍): {pin_place!r}")
        return pin_place

    doc = nlp(caption)
    for ent in doc.ents:
        if ent.label_ in ["FAC", "ORG", "LOC", "GPE"]:
            candidate = clean_candidate(ent.text)
            if is_valid_place(candidate) and candidate.lower() not in BAD_PLACE_WORDS:
                print(f"  Instagram name (NLP {ent.label_}): {candidate!r}")
                return candidate

    for pattern in [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Gardens|Cafe|Market|Park|Trail|Restaurant|Buffet|Mall|Waterfall|Centre|Center|Arena|Stadium|Gallery|Museum|Falls|Peak|Beach|Lookout|Viewpoint|Terrace|Square|Pier|Boardwalk))',
        r'(?:at|visit|to|from|in)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})',
        r'(?:spot|place|location)\s+(?:for|in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})',
    ]:
        for match in re.findall(pattern, caption):
            candidate = clean_candidate(match)
            if is_valid_place(candidate):
                print(f"  Instagram name (pattern): {candidate!r}")
                return candidate

    for chunk in doc.noun_chunks:
        text_chunk = chunk.text.strip()
        if (
            len(text_chunk.split()) >= 2
            and text_chunk[0].isupper()
            and is_valid_place(text_chunk)
            and text_chunk.lower() not in BAD_PLACE_WORDS
        ):
            candidate = clean_candidate(text_chunk)
            print(f"  Instagram name (noun chunk): {candidate!r}")
            return candidate

    print("  Instagram name: could not extract")
    return None


def build_queries(raw_name, city_context):
    cleaned = re.sub(r'(?i)\b(explore|visit|must|best|the|place|to|be|canada)\b', '', raw_name)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    queries = []
    if city_context:
        if "," in city_context:
            queries.append(f"{cleaned}, {city_context}")
        else:
            queries.append(f"{cleaned}, {city_context}, Ontario, Canada")
    queries.append(f"{cleaned}, Ontario, Canada")
    if not city_context or ("Toronto" not in city_context and "," not in city_context):
        queries.append(f"{cleaned}, Toronto, Ontario, Canada")
    queries.append(cleaned)
    seen = set()
    result = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            result.append(q)
    return result


def extract_artist(text, transcript, post):
    hashtag_artist_map = {
        "katseye": "KATSEYE", "latseye": "KATSEYE", "swaelee": "Swae Lee",
        "brunomars": "Bruno Mars", "danielcaesar": "Daniel Caesar", "zaralarsson": "Zara Larsson",
    }
    text_lower = text.lower()
    for tag_key, artist_val in hashtag_artist_map.items():
        if f"#{tag_key}" in text_lower:
            return artist_val
    at_mention = re.search(r'@([A-Za-z0-9]+)', text)
    if at_mention:
        for tag_key, artist_val in hashtag_artist_map.items():
            if tag_key in at_mention.group(1).lower():
                return artist_val
    mention_match = re.search(r'^@([A-Za-z0-9][A-Za-z0-9\s]{1,40}?)\s+(?=[A-Z]|\d)', text)
    if mention_match:
        candidate = re.sub(r'([a-z])([A-Z])', r'\1 \2', mention_match.group(1).strip())
        if not any(w in candidate.lower() for w in ["canada", "music", "official", "tv", "media"]):
            return candidate
    for source in [text, transcript]:
        if not source:
            continue
        for ent in nlp(source).ents:
            if ent.label_ == "PERSON" and len(ent.text.strip()) > 2:
                name = ent.text.strip()
                return name[1:].strip() if name.startswith("@") else name
    music_artist = post.get("music", {}).get("artist", "")
    if music_artist and music_artist.lower() not in {"original sound", "unknown"}:
        return music_artist
    return None


def address_is_confirmed(addresses, poi):
    if addresses:
        return True
    if poi and poi.get("address"):
        return bool(re.search(r'\d', poi["address"]))
    return False


def poi_address_is_specific(address: str) -> bool:
    """Return True only if the address has a street number (e.g. '288 Bremner Blvd ...')."""
    if not address:
        return False
    return bool(re.match(r'^\d', address.strip()))


def run():
    with open(os.path.join(BASE_DIR, "data/tiktok_posts.json"), "r", encoding="utf-8") as f:
        posts = json.load(f)

    already_done   = set()
    extracted_path = os.path.join(BASE_DIR, "data/extracted_places.json")
    existing_results = []
    if os.path.exists(extracted_path):
        with open(extracted_path, "r", encoding="utf-8") as f:
            existing_results = json.load(f)
        already_done = {r["tiktok_id"] for r in existing_results}

    results  = list(existing_results)
    seen_ids = set(already_done)

    for post in posts:
        post_id   = post.get("id") or post.get("tiktok_id")
        text      = post.get("description", "") or post.get("original_text", "")
        url       = post.get("url", "") or post.get("tiktok_url", "")
        post_type = post.get("type", "")

        if post_id in seen_ids:
            print(f"\nSkipping already-extracted: {post_id}")
            continue
        seen_ids.add(post_id)

        raw_trans  = post.get("transcript", "")
        transcript = strip_webvtt(raw_trans) if raw_trans else ""
        combined   = (text + " " + transcript).lower()

        print(f"\nProcessing: {post_id} (type={post_type!r})")

        # ------------------------------------------------------------------ #
        #  INSTAGRAM POSTS: dedicated extraction path                         #
        # ------------------------------------------------------------------ #
        if post_type == "instagram":
            print(f"  Instagram post — caption-based extraction")

            category = classify_post(text)
            hashtag_text = " ".join(post.get("hashtags", []))
            alias_query  = detect_alias(text + " " + hashtag_text)

            city_context = None
            for city in ["mississauga", "toronto", "brampton", "vaughan", "markham", "scarborough", "niagara falls", "hamilton"]:
                if city in combined:
                    city_context = city.title()
                    break
            if not city_context:
                for tag in post.get("hashtags", []):
                    if tag.lower() in HASHTAG_CITY_MAP:
                        city_context = HASHTAG_CITY_MAP[tag.lower()]
                        break

            enriched_name    = None
            enriched_address = None
            latitude         = None
            longitude        = None

            try:
                if alias_query:
                    if alias_query in ALIAS_FORCED_COORDS:
                        forced           = ALIAS_FORCED_COORDS[alias_query]
                        enriched_address = forced["address"]
                        latitude         = forced["latitude"]
                        longitude        = forced["longitude"]
                        enriched_name    = ALIAS_DISPLAY_NAMES.get(alias_query, alias_query.split(",")[0].strip())
                        print(f"  Alias (forced coords): {enriched_name!r}")
                    else:
                        loc = geocode(alias_query, addressdetails=True)
                        if loc:
                            enriched_address = loc.address
                            enriched_name    = ALIAS_DISPLAY_NAMES.get(alias_query, alias_query.split(",")[0].strip())
                            latitude         = loc.latitude
                            longitude        = loc.longitude
                            print(f"  Alias: {enriched_name!r}")

                if not enriched_name:
                    enriched_name = extract_instagram_name(text)

                if enriched_name and not enriched_address:
                    queries = build_queries(enriched_name, city_context)
                    for query in queries:
                        print(f"  Geocoding: {query!r}")
                        loc = geocode(query, addressdetails=True)
                        if loc and geocode_result_is_specific(loc):
                            enriched_address = loc.address
                            latitude         = loc.latitude
                            longitude        = loc.longitude
                            print(f"  Geocoded: {enriched_address!r}")
                            break
                        elif loc:
                            print(f"  Skipping vague result: {loc.address!r}")

                if not latitude and city_context:
                    city_key = city_context.split(",")[0].strip()
                    if city_key in CITY_FALLBACK_COORDS:
                        forced           = CITY_FALLBACK_COORDS[city_key]
                        enriched_address = forced["address"]
                        latitude         = forced["latitude"]
                        longitude        = forced["longitude"]
                        print(f"  City fallback: {city_key!r}")
                    else:
                        city_query = city_context if "," in city_context else f"{city_context}, Ontario, Canada"
                        loc = geocode(city_query, addressdetails=True)
                        if loc:
                            enriched_address = loc.address
                            latitude         = loc.latitude
                            longitude        = loc.longitude

            except GeocoderTimedOut:
                print("  Geocoder timeout.")

            results.append({
                "tiktok_id":           post_id,
                "tiktok_url":          url,
                "detected_city":       city_context,
                "original_text":       text,
                "transcript":          transcript,
                "category":            category,
                "artist_name":         None,
                "place_names":         [enriched_name] if enriched_name else [],
                "addresses":           [],
                "enriched_address":    enriched_address,
                "enriched_place_name": enriched_name,
                "latitude":            latitude,
                "longitude":           longitude,
            })

            print(f"  → {enriched_name!r} | {enriched_address!r}")
            continue

        # ------------------------------------------------------------------ #
        #  TIKTOK POSTS: original pipeline                                    #
        # ------------------------------------------------------------------ #

        handle_match  = re.search(r'tiktok\.com/@([A-Za-z0-9_.]+)/', url)
        tiktok_handle = handle_match.group(1).replace("_", " ").replace(".", " ").strip() if handle_match else ""

        video_text = ""
        if url and post_type != "photo":
            print(f"  Step 1/4: downloading video for OCR...")
            video_text = extract_video_text(url)
            if video_text:
                combined += " " + video_text.lower()
        else:
            print(f"  Step 1/4: skipping OCR (photo post)")

        print(f"  Step 2/4: detecting city and category...")

        city_context = None
        for city in ["mississauga", "toronto", "brampton", "vaughan", "markham", "scarborough", "niagara falls", "hamilton", "niagara-on-the-lake"]:
            if city in combined:
                city_context = city.title()
                break

        if not city_context:
            for tag in post.get("hashtags", []):
                if tag.lower() in HASHTAG_CITY_MAP:
                    city_context = HASHTAG_CITY_MAP[tag.lower()]
                    print(f"  Hashtag city: {city_context!r}")
                    break

        if not city_context:
            for keyword, city_val in HASHTAG_CITY_MAP.items():
                if f"#{keyword}" in text.lower() or f" {keyword} " in text.lower():
                    city_context = city_val
                    print(f"  Text city: {city_context!r}")
                    break

        hashtag_text = " ".join(post.get("hashtags", []))
        alias_query  = detect_alias(text + " " + hashtag_text + " " + transcript + " " + video_text)
        category     = classify_post(text + " " + hashtag_text)

        artist_name = None
        if category == "music":
            artist_name = extract_artist(text, transcript, post)
            if artist_name and artist_name.startswith("@"):
                artist_name = artist_name[1:].strip()
            if artist_name:
                print(f"  Artist detected: {artist_name}")

        print(f"  Step 3/4: extracting place candidates...")

        addresses        = extract_addresses(text) if category != "music" else []
        candidate_scores = extract_place_candidates(text, 3) if category != "music" else {}

        if video_text:
            ocr_scores = extract_place_candidates(video_text, 3)
            for k, v in ocr_scores.items():
                candidate_scores[k] = candidate_scores.get(k, 0) + v
            if not addresses and ocr_has_canadian_postal(video_text):
                addresses = extract_addresses(video_text)
                if addresses:
                    print(f"  OCR address (postal confirmed): {addresses}")

        top_desc_score      = max(candidate_scores.values(), default=0)
        description_is_weak = (not addresses) and (top_desc_score < 5)

        if transcript and description_is_weak:
            print(f"  Transcript fallback (score={top_desc_score})")
            t_scores = extract_place_candidates(transcript, 2)
            for k, v in t_scores.items():
                candidate_scores[k] = candidate_scores.get(k, 0) + v

        if transcript and not addresses:
            addresses = extract_addresses(transcript)

        def place_sort_key(item):
            score = item[1]
            if category == "nature" and NATURE_LANDMARK_RE.search(item[0]):
                score += 4
            return score

        sorted_places = sorted(candidate_scores.items(), key=place_sort_key, reverse=True)
        place_names   = [p[0] for p in sorted_places]
        place_names   = [p for p in place_names if p.lower() not in {"nashville", "toronto", "mississauga", "canada", "ontario"}]

        filtered_places = []
        for candidate in place_names:
            if not any(candidate.lower() in ex.lower() for ex in filtered_places):
                filtered_places.append(candidate)
        place_names = [PLACE_NAME_OVERRIDES.get(p.lower(), p) for p in filtered_places]

        print(f"  Step 4/4: geocoding...")

        enriched_address = None
        enriched_name    = None
        poi_place_name   = None
        alias_place_name = None
        latitude         = None
        longitude        = None
        alias_fired      = False

        # ------------------------------------------------------------------ #
        #  PHOTO POSTS                                                        #
        # ------------------------------------------------------------------ #
        if post_type == "photo":
            print(f"  Photo post — description-only extraction")

            PLACE_SUFFIX_RE = re.compile(
                r'(park|garden|gardens|falls|beach|trail|market|cafe|restaurant|'
                r'mall|centre|center|museum|gallery|arena|district|island|ravine|'
                r'conservation|lookout|pier|boardwalk|square|village)$',
                re.IGNORECASE
            )
            PLACE_SUFFIX_RE = re.compile(
                r'(park|garden|gardens|falls|beach|trail|market|cafe|restaurant|'
                r'mall|centre|center|museum|gallery|arena|district|island|ravine|'
                r'conservation|lookout|pier|boardwalk|square|village)$',
                re.IGNORECASE
            )
            for hashtag in post.get("hashtags", []):
                ht_lower = hashtag.lower()
                if ht_lower in BAD_PLACE_WORDS:
                    continue
                if PLACE_SUFFIX_RE.search(ht_lower):
                    # Split camelCase or treat whole thing as place
                    spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', hashtag).title()
                    candidate = clean_candidate(spaced)
                    if is_valid_place(candidate):
                        candidate_scores[candidate] = candidate_scores.get(candidate, 0) + 4
                        print(f"  Photo hashtag place: {candidate!r}")
            try:
                if alias_query:
                    if alias_query in ALIAS_FORCED_COORDS:
                        forced           = ALIAS_FORCED_COORDS[alias_query]
                        enriched_address = forced["address"]
                        latitude         = forced["latitude"]
                        longitude        = forced["longitude"]
                        enriched_name    = ALIAS_DISPLAY_NAMES.get(alias_query, alias_query.split(",")[0].strip())
                        print(f"  Alias (forced coords): {enriched_name!r}")
                    else:
                        loc = geocode(alias_query, addressdetails=True)
                        if loc:
                            enriched_address = loc.address
                            enriched_name    = ALIAS_DISPLAY_NAMES.get(alias_query, alias_query.split(",")[0].strip())
                            latitude         = loc.latitude
                            longitude        = loc.longitude

                if not enriched_address and addresses:
                    for addr in addresses:
                        loc = geocode(addr, addressdetails=True)
                        if loc:
                            enriched_address = loc.address
                            latitude         = loc.latitude
                            longitude        = loc.longitude
                            enriched_name    = place_names[0] if place_names else loc.raw.get("display_name", "").split(",")[0]
                            break

                if not enriched_name and place_names and max(candidate_scores.values(), default=0) >= 5:
                    enriched_name = place_names[0]

            except GeocoderTimedOut:
                print("  Geocoder timeout.")

            print(f"  Photo post done. Name: {enriched_name!r} | Address: {enriched_address!r}")

        # ------------------------------------------------------------------ #
        #  VIDEO POSTS                                                        #
        # ------------------------------------------------------------------ #
        else:
            try:
                location = None
                poi = post.get("poi")

                if poi and poi.get("address"):
                    poi_address_str = poi["address"]
                    poi_name_str    = poi.get("name", "")
                    if poi_address_is_specific(poi_address_str):
                        print(f"  POI address (specific): {poi_address_str!r}")
                        location = geocode(poi_address_str, addressdetails=True)
                        if location:
                            enriched_address = poi_address_str
                            poi_place_name   = poi_name_str or location.raw.get("name", "")
                            enriched_name    = poi_place_name
                            latitude         = location.latitude
                            longitude        = location.longitude
                    else:
                        # Vague address — geocode by POI name for accuracy
                        print(f"  POI address vague ({poi_address_str!r}), geocoding by name: {poi_name_str!r}")
                        if poi_name_str:
                            location = geocode(poi_name_str, addressdetails=True)
                            if location:
                                enriched_address = location.address
                                poi_place_name   = poi_name_str
                                enriched_name    = poi_name_str
                                latitude         = location.latitude
                                longitude        = location.longitude

                if not location and alias_query:
                    print(f"  Alias: {alias_query}")
                    if alias_query in ALIAS_FORCED_COORDS:
                        forced           = ALIAS_FORCED_COORDS[alias_query]
                        enriched_address = forced["address"]
                        latitude         = forced["latitude"]
                        longitude        = forced["longitude"]
                        alias_place_name = ALIAS_DISPLAY_NAMES.get(alias_query, alias_query.split(",")[0].strip())
                        enriched_name    = alias_place_name
                        alias_fired      = True
                        location         = True
                        print(f"  Alias (forced coords): {enriched_name!r}")
                    else:
                        location = geocode(alias_query, addressdetails=True)
                        if location:
                            enriched_address = location.address
                            alias_place_name = ALIAS_DISPLAY_NAMES.get(alias_query, alias_query.split(",")[0].strip())
                            enriched_name    = alias_place_name
                            latitude         = location.latitude
                            longitude        = location.longitude
                            alias_fired      = True

                if not location and addresses:
                    raw_address = addresses[0]
                    print(f"  Address: {raw_address!r}")
                    for addr in list(dict.fromkeys([
                        raw_address,
                        re.sub(r'\s+Unit\s+\w+', '', raw_address, flags=re.IGNORECASE),
                        re.sub(r'[A-Z]\d[A-Z]\s?\d[A-Z]\d', '', raw_address, flags=re.IGNORECASE),
                    ])):
                        location = geocode(addr, addressdetails=True)
                        if location:
                            break
                    if location:
                        enriched_address = location.address
                        latitude         = location.latitude
                        longitude        = location.longitude
                        enriched_name    = place_names[0] if place_names else location.raw.get("display_name", "").split(",")[0]

                confirmed = address_is_confirmed(addresses, poi) or alias_fired

                ocr_location_hint = None
                if video_text:
                    at_m = re.search(r'@\s*([A-Za-z0-9\s&\'.,\-]{3,80})(?:\n|$)', video_text)
                    if at_m:
                        hint = at_m.group(1).strip()
                        if any(s in hint.lower() for s in ["toronto", "mississauga", "brampton", "st", "ave", "road", "blvd", "bay", "king", "queen", "yonge", "street"]):
                            ocr_location_hint = hint

                if place_names and category != "music" and not confirmed:
                    for raw_name in place_names:
                        queries = []
                        if ocr_location_hint and raw_name == place_names[0]:
                            combined_query = re.sub(r'\s+', ' ', re.sub(r'(?i)\b(canada)\b', '', f"{raw_name} {ocr_location_hint}")).strip()
                            queries += [f"{combined_query}, Ontario, Canada", combined_query]
                        queries.extend(build_queries(raw_name, city_context))
                        place_location = None
                        for query in queries:
                            print(f"  Place: {query!r}")
                            place_location = geocode(query, addressdetails=True)
                            if place_location and geocode_result_is_specific(place_location):
                                break
                            elif place_location:
                                print(f"  Skipping vague result: {place_location.address!r}")
                                place_location = None
                        if place_location:
                            enriched_address = place_location.address
                            enriched_name    = raw_name
                            latitude         = place_location.latitude
                            longitude        = place_location.longitude
                            location         = place_location
                            break
                        else:
                            enriched_name = raw_name

                elif place_names and category != "music" and confirmed:
                    enriched_name = place_names[0] if place_names else alias_place_name
                    print(f"  Confirmed, skipping place geocode. Name: {enriched_name!r}")

                elif not location and place_names:
                    for raw_name in place_names:
                        queries = []
                        if ocr_location_hint and raw_name == place_names[0]:
                            combined_query = re.sub(r'\s+', ' ', re.sub(r'(?i)\b(canada)\b', '', f"{raw_name} {ocr_location_hint}")).strip()
                            queries += [f"{combined_query}, Ontario, Canada", combined_query]
                        queries.extend(build_queries(raw_name, city_context))
                        for query in queries:
                            print(f"  Place: {query!r}")
                            location = geocode(query, addressdetails=True)
                            if location:
                                enriched_address = location.address
                                enriched_name    = location.raw.get("name") or raw_name
                                latitude         = location.latitude
                                longitude        = location.longitude
                                break
                        if location:
                            break

                if not location and city_context and category != "music":
                    city_key = city_context.split(",")[0].strip()
                    if city_key in CITY_FALLBACK_COORDS:
                        forced           = CITY_FALLBACK_COORDS[city_key]
                        enriched_address = forced["address"]
                        latitude         = forced["latitude"]
                        longitude        = forced["longitude"]
                        if not enriched_name:
                            enriched_name = place_names[0] if place_names else None
                        print(f"  City fallback (forced): {city_key!r} → {enriched_name!r}")
                    else:
                        city_query = city_context if "," in city_context else f"{city_context}, Ontario, Canada"
                        print(f"  City fallback (geocode): {city_query!r}")
                        city_location = geocode(city_query, addressdetails=True)
                        if city_location:
                            enriched_address = city_location.address
                            latitude         = city_location.latitude
                            longitude        = city_location.longitude
                            if not enriched_name:
                                enriched_name = place_names[0] if place_names else None

            except GeocoderTimedOut:
                print("  Geocoder timeout.")

        # --- Cleanup ---
        if category == "music":
            enriched_name = artist_name or poi_place_name

        if enriched_name and enriched_name.lower() in PLACE_NAME_OVERRIDES:
            enriched_name = PLACE_NAME_OVERRIDES[enriched_name.lower()]
        if enriched_name and enriched_name.startswith("@"):
            enriched_name = enriched_name[1:].strip()

        results.append({
            "tiktok_id":           post_id,
            "tiktok_url":          url,
            "detected_city":       city_context,
            "original_text":       text,
            "transcript":          transcript,
            "category":            category,
            "artist_name":         artist_name,
            "place_names":         place_names,
            "addresses":           addresses,
            "enriched_address":    enriched_address,
            "enriched_place_name": enriched_name,
            "latitude":            latitude,
            "longitude":           longitude,
        })

        print(f"  → {enriched_name!r} | {enriched_address!r}")

    output_path = os.path.join(BASE_DIR, "data", "extracted_places.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"\nDone! Saved {len(results)} results to {output_path}")


if __name__ == "__main__":
    run()