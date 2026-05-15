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

nlp = spacy.load("en_core_web_trf")

geolocator = Nominatim(user_agent="tiktok_place_extractor")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

with open("backend/data/tiktok_posts.json", "r", encoding="utf-8") as f:
    posts = json.load(f)

# --- Address regex ---
# Negative lookbehind on digits prevents matching years (e.g. 2024 Something Rd).
# The optional suffix groups handle unit numbers and multi-part city strings.
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

FAKE_ADDRESS_BLACKLIST = {
    "1 free dr",
    "1 free drive",
}

# --- Address validation ---
def is_real_address(addr: str) -> bool:
    if not addr:
        return False
    if addr.strip().lower() in FAKE_ADDRESS_BLACKLIST:
        return False
    if len(addr) > 120:
        return False
    street_types = r'\b(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b'
    if not re.search(street_types, addr, re.IGNORECASE):
        return False
    if not re.match(r'^\d', addr.strip()):
        return False
    if '\n' in addr:
        return False
    return True

# --- Known venue aliases ---
# Maps common shorthand / hashtag forms to a canonical geocodable string.
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
}

# Nominatim returns a bad centroid for Canada's Wonderland; hard-code the real entrance.
ALIAS_FORCED_COORDS = {
    "Canada's Wonderland, Vaughan, Ontario": {
        "address":   "Canada's Wonderland, 1 Canada's Wonderland Drive, Vaughan, Ontario, L6A 1S6, Canada",
        "latitude":  43.8430,
        "longitude": -79.5390,
    },
}

def detect_alias(text):
    text_lower = text.lower()
    for keyword, canonical in PLACE_ALIASES.items():
        if keyword in text_lower:
            return canonical
    return None

# Concert hashtags — "romafterdark" intentionally excluded here;
# it's an attractions post and should go through keyword scoring instead.
CONCERT_HASHTAGS_RE = re.compile(
    r'#(concert|tour|liveshow|liveevent|theromantictour)',
    re.IGNORECASE
)

# --- Category keyword lists ---
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

# Words that look like place names but aren't useful for geocoding.
BAD_PLACE_WORDS = {
    "google", "toronto", "canada", "ontario",
    "mississauga", "thailand", "bangkok",
    "always", "never", "live", "baby", "alway",
    "tesla",
}

# Maps city-level hashtags to a canonical geocodable string.
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

# Hard-coded city centroids for local cities.
# Nominatim often resolves these to regional boundaries (e.g. "Peel, Ontario")
# rather than useful city-centre coordinates.
CITY_FALLBACK_COORDS = {
    "Mississauga": {
        "address":   "Mississauga, Ontario, Canada",
        "latitude":  43.5890,
        "longitude": -79.6441,
    },
    "Brampton": {
        "address":   "Brampton, Ontario, Canada",
        "latitude":  43.7315,
        "longitude": -79.7624,
    },
    "Vaughan": {
        "address":   "Vaughan, Ontario, Canada",
        "latitude":  43.8361,
        "longitude": -79.4983,
    },
    "Toronto": {
        "address":   "Toronto, Ontario, Canada",
        "latitude":  43.6532,
        "longitude": -79.3832,
    },
    "Hamilton": {
        "address":   "Hamilton, Ontario, Canada",
        "latitude":  43.2557,
        "longitude": -79.8711,
    },
    "Niagara Falls": {
        "address":   "Niagara Falls, Ontario, Canada",
        "latitude":  43.0962,
        "longitude": -79.0377,
    },
}

# Nominatim can resolve a venue name to an administrative boundary rather than
# a specific point. Reject those results so we keep looking for something better.
def geocode_result_is_specific(location) -> bool:
    if not location:
        return False
    raw_type  = location.raw.get("type", "")
    osm_class = location.raw.get("class", "")
    vague_types = {
        "administrative", "county", "region", "municipality",
        "city", "town", "village", "suburb",
    }
    if raw_type in vague_types:
        return False
    if osm_class in {"boundary", "place"} and raw_type in vague_types:
        return False
    return True

# --- Strip WebVTT metadata from auto-captions ---
def strip_webvtt(text):
    text = re.sub(r'^WEBVTT\b.*$', '', text, flags=re.MULTILINE)
    text = re.sub(
        r'\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[\.,]\d{3}[^\n]*',
        '', text
    )
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()

# --- OCR text overlay frames from a TikTok video ---
def extract_video_text(url, num_frames=6, max_seconds=15):
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

# --- Category classifier ---
def classify_post(text):
    if CONCERT_HASHTAGS_RE.search(text):
        return "music"
    text_lower = text.lower()
    scores = {
        cat: sum(1 for kw in kws if kw in text_lower)
        for cat, kws in CATEGORY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return "unknown" if scores[best] == 0 else best

def clean_candidate(text):
    text = text.strip()
    text = re.sub(r'[^\w\s&\'.,-]', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip(" -,|@.")
    return text

def is_valid_place(candidate):
    if not candidate:
        return False
    cl = candidate.lower()
    if len(candidate) < 3:
        return False
    if len(candidate.split()) > 6:
        return False
    # Filter out things that look like ticker symbols / postal codes
    if re.match(r'^[A-Z]{2}\s*[A-Z0-9]+$', candidate):
        return False
    if cl in BAD_PLACE_WORDS:
        return False
    bad_phrases = [
        "the place to be", "if youre", "along the way",
        "must visit", "picture-perfect",
    ]
    return not any(p in cl for p in bad_phrases)

def extract_addresses(text):
    return [a for a in address_pattern.findall(text) if is_real_address(a)]

# Boost score for nature-specific landmark suffixes so they beat generic NER hits.
NATURE_LANDMARK_RE = re.compile(
    r'\b(falls?|peak|gorge|ravine|gardens?|conservation\s+area|trail|beach|cove)\b',
    re.IGNORECASE
)

# --- Multi-signal place candidate extraction ---
def extract_place_candidates(text, score_boost=2):
    doc = nlp(text)
    local_scores = {}

    # Food-related words get a score bump — they're strong signals for a restaurant name.
    business_words = [
        "chicken", "cafe", "restaurant", "bbq", "burger",
        "pizza", "ramen", "sushi", "hot", "donut", "donuts",
        "birria", "taco", "tacos",
    ]

    def add_local(candidate, score):
        if not is_valid_place(candidate):
            return
        for word in business_words:
            if word in candidate.lower():
                score += 3
        local_scores[candidate] = local_scores.get(candidate, 0) + score

    # Explicit "Place:" label — highest confidence
    place_match = re.search(r'(?i)place:\s*([^:\n]+?)(?:location:|$)', text)
    if place_match:
        add_local(clean_candidate(place_match.group(1)), 5)

    # Pin emoji — strong intent signal
    pin_match = re.search(r'📍\s*([A-Za-z0-9\s&\'.,-]{3,60})', text)
    if pin_match:
        add_local(clean_candidate(pin_match.group(1)), 4)

    # @ mention followed by a recognisable street keyword
    at_match = re.search(r'@\s*([A-Za-z0-9\s&\'.,-]{3,80})(?:\n|$)', text)
    if at_match:
        candidate = clean_candidate(at_match.group(1))
        location_hints = [
            "toronto", "mississauga", "brampton", "st", "ave",
            "road", "blvd", "bay", "king", "queen", "yonge",
        ]
        if any(h in candidate.lower() for h in location_hints):
            add_local(candidate, 5)

    # spaCy NER
    for ent in doc.ents:
        if ent.label_ in ["FAC", "ORG", "LOC"]:
            add_local(clean_candidate(ent.text), score_boost)

    # Custom regex patterns for venue name formats spaCy misses
    custom_patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Gardens|Cafe|Market|Park|Trail|Restaurant|Buffet|Mall|Waterfall|Centre|Center|Arena|Stadium|Gallery|Museum|Falls|Peak))',
        r'(?:at|visit|to)\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})',
    ]
    for pattern in custom_patterns:
        for match in re.findall(pattern, text):
            add_local(clean_candidate(match), score_boost)

    # CamelCase hashtags are often brand/venue names
    for hashtag in re.findall(r'#([A-Za-z]{4,})', text):
        if len(hashtag) >= 6 and hashtag.lower() not in BAD_PLACE_WORDS:
            spaced = re.sub(r'([a-z])([A-Z])', r'\1 \2', hashtag)
            if spaced != hashtag:
                add_local(clean_candidate(spaced), 2)

    # When a lowercase hashtag matches the @-handle exactly, it's almost certainly
    # the brand name (e.g. @tejasbirria + #tejasbirria).
    at_handle_in_text = re.search(r'@([A-Za-z0-9]{4,})', text)
    if at_handle_in_text:
        handle_lower = at_handle_in_text.group(1).lower()
        for hashtag in re.findall(r'#([A-Za-z]{4,})', text):
            if hashtag.lower() == handle_lower:
                titled = hashtag.title()
                add_local(titled, 4)

    return local_scores

# --- Build a prioritised list of geocode query strings ---
def build_queries(raw_name, city_context):
    cleaned = re.sub(
        r'(?i)\b(explore|visit|must|best|the|place|to|be|canada)\b',
        '', raw_name
    )
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

    # Deduplicate while preserving order
    seen = set()
    result = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            result.append(q)
    return result

# --- Identify the performing artist for music posts ---
def extract_artist(text, transcript, post):
    hashtag_artist_map = {
        "katseye":      "KATSEYE",
        "latseye":      "KATSEYE",
        "swaelee":      "Swae Lee",
        "brunomars":    "Bruno Mars",
        "danielcaesar": "Daniel Caesar",
        "zaralarsson":  "Zara Larsson",
    }
    text_lower = text.lower()
    for tag_key, artist_val in hashtag_artist_map.items():
        if f"#{tag_key}" in text_lower:
            return artist_val

    at_mention = re.search(r'@([A-Za-z0-9]+)', text)
    if at_mention:
        mention_lower = at_mention.group(1).lower()
        for tag_key, artist_val in hashtag_artist_map.items():
            if tag_key in mention_lower:
                return artist_val

    mention_match = re.search(r'^@([A-Za-z0-9][A-Za-z0-9\s]{1,40}?)\s+(?=[A-Z]|\d)', text)
    if mention_match:
        candidate = mention_match.group(1).strip()
        candidate = re.sub(r'([a-z])([A-Z])', r'\1 \2', candidate)
        if not any(w in candidate.lower() for w in ["canada", "music", "official", "tv", "media"]):
            return candidate

    for source in [text, transcript]:
        if not source:
            continue
        doc = nlp(source)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                if len(name) > 2:
                    # Strip any leading @ that spaCy included in the entity span
                    if name.startswith("@"):
                        name = name[1:].strip()
                    return name

    music_artist = post.get("music", {}).get("artist", "")
    if music_artist and music_artist.lower() not in {"original sound", "unknown"}:
        return music_artist

    return None

def address_is_confirmed(addresses, poi):
    if addresses:
        return True
    if poi and poi.get("address"):
        addr = poi["address"]
        return bool(re.search(r'\d', addr))
    return False

PLACE_NAME_OVERRIDES = {
    "rom":                "Royal Ontario Museum",
    "royalontariomuseum": "Royal Ontario Museum",
}

# --- Main processing loop ---
results = []
seen_ids = set()

for post in posts:

    post_id = post.get("id") or post.get("tiktok_id")
    text    = post.get("description", "") or post.get("original_text", "")
    url     = post.get("url", "") or post.get("tiktok_url", "")

    if post_id in seen_ids:
        print(f"\nSkipping duplicate: {post_id}")
        continue
    seen_ids.add(post_id)

    raw_trans  = post.get("transcript", "")
    transcript = strip_webvtt(raw_trans) if raw_trans else ""
    combined   = (text + " " + transcript).lower()

    print(f"\nProcessing: {post_id}")

    # Pull the handle from the URL for use as a brand-name fallback on food posts.
    handle_match = re.search(r'tiktok\.com/@([A-Za-z0-9_.]+)/', url)
    tiktok_handle = (
        handle_match.group(1).replace("_", " ").replace(".", " ").strip()
        if handle_match else ""
    )

    video_text = ""
    if url:
        video_text = extract_video_text(url)
        if video_text:
            combined += " " + video_text.lower()
    else:
        print("  No URL — skipping OCR")

    # --- Detect city context ---
    city_context = None

    known_cities = [
        "mississauga", "toronto", "brampton", "vaughan",
        "markham", "scarborough", "niagara falls", "hamilton",
        "niagara-on-the-lake",
    ]
    for city in known_cities:
        if city in combined:
            city_context = city.title()
            break

    if not city_context:
        for tag in post.get("hashtags", []):
            tag_lower = tag.lower()
            if tag_lower in HASHTAG_CITY_MAP:
                city_context = HASHTAG_CITY_MAP[tag_lower]
                print(f"  Hashtag city: {city_context!r}")
                break

    if not city_context:
        desc_lower = text.lower()
        for keyword, city_val in HASHTAG_CITY_MAP.items():
            if f"#{keyword}" in desc_lower or f" {keyword} " in desc_lower:
                city_context = city_val
                print(f"  Text city: {city_context!r}")
                break

    # --- Alias detection ---
    hashtag_text = " ".join(post.get("hashtags", []))
    alias_query  = detect_alias(text + " " + hashtag_text + " " + transcript + " " + video_text)

    # --- Classify ---
    category = classify_post(text + " " + hashtag_text)

    # --- Artist detection (music posts only) ---
    artist_name = None
    if category == "music":
        artist_name = extract_artist(text, transcript, post)
        # Safety strip — prevent any stray @ making it into the output
        if artist_name and artist_name.startswith("@"):
            artist_name = artist_name[1:].strip()
        if artist_name:
            print(f"  Artist detected: {artist_name}")

    # --- Extraction ---
    addresses        = extract_addresses(text) if category != "music" else []
    candidate_scores = extract_place_candidates(text, 3) if category != "music" else {}

    if video_text:
        ocr_scores = extract_place_candidates(video_text, 3)
        for k, v in ocr_scores.items():
            candidate_scores[k] = candidate_scores.get(k, 0) + v
        # Only trust OCR addresses when a postal code is present — reduces false positives.
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

    # --- Rank candidates ---
    def place_sort_key(item):
        score = item[1]
        if category == "nature" and NATURE_LANDMARK_RE.search(item[0]):
            score += 4
        return score

    sorted_places = sorted(candidate_scores.items(), key=place_sort_key, reverse=True)
    place_names   = [p[0] for p in sorted_places]

    filtered_city_words = {"nashville", "toronto", "mississauga", "canada", "ontario"}
    place_names = [p for p in place_names if p.lower() not in filtered_city_words]

    # Remove near-duplicates (keep the more specific one)
    filtered_places = []
    for candidate in place_names:
        if not any(candidate.lower() in ex.lower() for ex in filtered_places):
            filtered_places.append(candidate)
    place_names = filtered_places

    place_names = [PLACE_NAME_OVERRIDES.get(p.lower(), p) for p in place_names]

    # If nothing surfaced for a food post, fall back to the creator's handle —
    # restaurant accounts usually match their business name.
    if not place_names and category == "food" and tiktok_handle:
        handle_titled = tiktok_handle.title()
        if handle_titled.lower() not in BAD_PLACE_WORDS:
            place_names = [handle_titled]
            candidate_scores[handle_titled] = 2
            print(f"  Handle fallback: {handle_titled!r}")

    # --- Geocode / enrich ---
    enriched_address  = None
    enriched_name     = None
    poi_place_name    = None
    alias_place_name  = None
    latitude          = None
    longitude         = None
    alias_fired       = False

    try:
        location = None

        # Priority -1: TikTok POI tag (most authoritative source)
        poi = post.get("poi")
        if poi and poi.get("address"):
            poi_address_str = poi["address"]
            print(f"  POI address: {poi_address_str!r}")
            location = geocode(poi_address_str, addressdetails=True)
            if location:
                enriched_address = poi_address_str
                poi_place_name   = poi.get("name") or location.raw.get("name", "")
                enriched_name    = poi_place_name
                latitude         = location.latitude
                longitude        = location.longitude

        # Priority 0: Alias match
        if not location and alias_query:
            print(f"  Alias: {alias_query}")

            if alias_query in ALIAS_FORCED_COORDS:
                forced = ALIAS_FORCED_COORDS[alias_query]
                enriched_address = forced["address"]
                latitude         = forced["latitude"]
                longitude        = forced["longitude"]
                alias_place_name = ALIAS_DISPLAY_NAMES.get(
                    alias_query, alias_query.split(",")[0].strip()
                )
                enriched_name    = alias_place_name
                alias_fired      = True
                location         = True  # sentinel — prevents falling through to lower priorities
                print(f"  Alias (forced coords): {enriched_name!r}")
            else:
                location = geocode(alias_query, addressdetails=True)
                if location:
                    enriched_address = location.address
                    alias_place_name = ALIAS_DISPLAY_NAMES.get(
                        alias_query,
                        alias_query.split(",")[0].strip()
                    )
                    enriched_name    = alias_place_name
                    latitude         = location.latitude
                    longitude        = location.longitude
                    alias_fired      = True

        # Priority 1: Street address
        if not location and addresses:
            raw_address = addresses[0]
            print(f"  Address: {raw_address!r}")
            search_addresses = list(dict.fromkeys([
                raw_address,
                re.sub(r'\s+Unit\s+\w+', '', raw_address, flags=re.IGNORECASE),
                re.sub(r'[A-Z]\d[A-Z]\s?\d[A-Z]\d', '', raw_address, flags=re.IGNORECASE),
            ]))
            for addr in search_addresses:
                location = geocode(addr, addressdetails=True)
                if location:
                    break
            if location:
                enriched_address = location.address
                latitude         = location.latitude
                longitude        = location.longitude
                enriched_name    = (
                    place_names[0] if place_names
                    else location.raw.get("display_name", "").split(",")[0]
                )

        # Priority 2: Place name candidates
        # Skip geocoding when we already have a confirmed location (POI, alias, or address);
        # just pick the best display name from the candidates.
        confirmed = address_is_confirmed(addresses, poi) or alias_fired

        ocr_location_hint = None
        if video_text:
            at_match = re.search(
                r'@\s*([A-Za-z0-9\s&\'.,\-]{3,80})(?:\n|$)',
                video_text
            )
            if at_match:
                hint = at_match.group(1).strip()
                location_signals = [
                    "toronto", "mississauga", "brampton", "st", "ave",
                    "road", "blvd", "bay", "king", "queen", "yonge", "street",
                ]
                if any(s in hint.lower() for s in location_signals):
                    ocr_location_hint = hint

        if place_names and category != "music" and not confirmed:
            for raw_name in place_names:
                queries = []
                if ocr_location_hint and raw_name == place_names[0]:
                    combined_query = f"{raw_name} {ocr_location_hint}"
                    cleaned = re.sub(r'(?i)\b(canada)\b', '', combined_query)
                    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                    queries.append(f"{cleaned}, Ontario, Canada")
                    queries.append(cleaned)
                queries.extend(build_queries(raw_name, city_context))

                place_location = None
                for query in queries:
                    print(f"  Place: {query!r}")
                    place_location = geocode(query, addressdetails=True)
                    # Skip vague results and keep trying with the next query
                    if place_location and geocode_result_is_specific(place_location):
                        break
                    elif place_location:
                        print(f"  Skipping vague result for {query!r}: {place_location.address!r}")
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
            # Location is locked — use the top candidate as the display name.
            if place_names:
                enriched_name = place_names[0]
            elif not enriched_name:
                enriched_name = alias_place_name
            print(f"  Confirmed, skipping place geocode. Name: {enriched_name!r}")

        elif not location and place_names:
            for raw_name in place_names:
                queries = []
                if ocr_location_hint and raw_name == place_names[0]:
                    combined_query = f"{raw_name} {ocr_location_hint}"
                    cleaned = re.sub(r'(?i)\b(canada)\b', '', combined_query)
                    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                    queries.append(f"{cleaned}, Ontario, Canada")
                    queries.append(cleaned)
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

        # Priority 3: City-level fallback when no specific venue was found.
        if not location and city_context:
            city_key = city_context.split(",")[0].strip()
            if city_key in CITY_FALLBACK_COORDS:
                forced = CITY_FALLBACK_COORDS[city_key]
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

    if category == "music":
        if artist_name:
            enriched_name = artist_name
        elif poi_place_name:
            enriched_name = poi_place_name

    if enriched_name and enriched_name.lower() in PLACE_NAME_OVERRIDES:
        enriched_name = PLACE_NAME_OVERRIDES[enriched_name.lower()]

    # Final safety strip — belt-and-suspenders in case any path above missed it.
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

# --- Save results ---
output_path = r"backend\data\extracted_places.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"\nDone! Saved {len(results)} results to {output_path}")