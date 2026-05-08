import json
import re
import spacy
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.extra.rate_limiter import RateLimiter

# LOAD NLP MODEL
nlp = spacy.load("en_core_web_trf")

# GEOCODER
geolocator = Nominatim(
    user_agent="tiktok_place_extractor"
)

# RATE LIMITED GEOCODER
geocode = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1
)

# LOAD POSTS
with open(
    "backend/data/tiktok_posts.json",
    "r",
    encoding="utf-8"
) as f:

    posts = json.load(f)

# ADDRESS REGEX
address_pattern = re.compile(
    r'\d{1,6}\s+[A-Za-z0-9\s,.-]+'
    r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)'
    r'(?:\s+[NSEW])?'
    r'(?:\s+Unit\s+\w+)?'
    r'(?:,\s*[A-Za-z0-9\s-]+)*',
    re.IGNORECASE
)

# =========================
# CATEGORY KEYWORDS
# =========================
CATEGORY_KEYWORDS = {

    "food": [
        "food",
        "restaurant",
        "buffet",
        "dessert",
        "cafe",
        "eat",
        "burger",
        "pizza",
        "ramen",
        "sushi",
        "brunch",
        "streetfood",
        "drink",
        "bbq",
        "coffee",
        "bakery",
        "night market"
    ],

    "shopping": [
        "mall",
        "shopping",
        "store",
        "plaza",
        "marketplace"
    ],

    "nightlife": [
        "bar",
        "club",
        "nightlife",
        "party",
        "pub",
        "cocktail",
        "rooftop"
    ],

    "nature": [
        "park",
        "beach",
        "lake",
        "trail",
        "mountain",
        "hiking",
        "waterfall",
        "rainforest",
        "tree",
        "blossom"
    ]
}

# =========================
# BAD WORDS
# =========================
BAD_PLACE_WORDS = {
    "google",
    "toronto",
    "canada",
    "ontario",
    "mississauga",
    "thailand",
    "bangkok"
}

# =========================
# CLASSIFIER FUNCTION
# =========================
def classify_post(text):

    text = text.lower()

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in text:
                score += 1

        scores[category] = score

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "unknown"

    return best_category

# =========================
# CLEAN FUNCTION
# =========================
def clean_candidate(text):

    text = text.strip()

    # REMOVE EMOJIS / SPECIAL CHARS
    text = re.sub(
        r'[^\w\s&\'.,-]',
        '',
        text
    )

    # REMOVE HASHTAGS
    text = re.sub(
        r'#\w+',
        '',
        text
    )

    # SPLIT CAMELCASE
    text = re.sub(
        r'([a-z])([A-Z])',
        r'\1 \2',
        text
    )

    # COLLAPSE SPACES
    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    text = text.strip(" -,|@.")

    return text

# =========================
# VALIDATION FUNCTION
# =========================
def is_valid_place(candidate):

    if not candidate:
        return False

    candidate_lower = candidate.lower()

    # TOO SHORT
    if len(candidate) < 3:
        return False

    # TOO MANY WORDS
    if len(candidate.split()) > 6:
        return False

    # POSTAL CODE FRAGMENTS
    if re.match(
        r'^[A-Z]{2}\s*[A-Z0-9]+$',
        candidate
    ):
        return False

    # BAD WORDS
    if candidate_lower in BAD_PLACE_WORDS:
        return False

    # BAD PHRASES
    bad_phrases = [
        "the place to be",
        "if youre",
        "along the way",
        "must visit",
        "picture-perfect"
    ]

    for phrase in bad_phrases:

        if phrase in candidate_lower:
            return False

    return True

# =========================
# EXTRACT ADDRESSES
# =========================
def extract_addresses(text):

    return address_pattern.findall(text)

# =========================
# EXTRACT PLACE CANDIDATES
# =========================
def extract_place_candidates(
    text,
    score_boost=2
):

    doc = nlp(text)

    local_scores = {}

    def add_local(candidate, score):

        if not is_valid_place(candidate):
            return

        business_words = [
            "chicken",
            "cafe",
            "restaurant",
            "bbq",
            "burger",
            "pizza",
            "ramen",
            "sushi",
            "hot"
        ]

        candidate_lower = candidate.lower()

        for word in business_words:

            if word in candidate_lower:
                score += 3


        local_scores[candidate] = (
            local_scores.get(candidate, 0)
            + score
        )

    # --------------------------------
    # METHOD 1 → PLACE:
    # --------------------------------
    place_match = re.search(
        r'(?i)place:\s*([^:\n]+?)(?:location:|$)',
        text
    )

    if place_match:

        candidate = clean_candidate(
            place_match.group(1)
        )

        add_local(candidate, 5)

    # --------------------------------
    # METHOD 2 → 📍
    # --------------------------------
    pin_match = re.search(
        r'📍\s*([A-Za-z0-9\s&\'.,-]{3,60})',
        text
    )

    if pin_match:

        candidate = clean_candidate(
            pin_match.group(1)
        )

        add_local(candidate, 4)

    # --------------------------------
    # METHOD 3 → spaCy NER
    # --------------------------------
    for ent in doc.ents:

        if ent.label_ in [
            "FAC",
            "ORG",
            "LOC"
        ]:

            candidate = clean_candidate(
                ent.text
            )

            add_local(
                candidate,
                score_boost
            )

    # --------------------------------
    # METHOD 4 → CUSTOM PATTERNS
    # --------------------------------
    custom_patterns = [

        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Gardens|Cafe|Market|Park|Trail|Restaurant|Buffet|Mall|Waterfall))',

    ]

    for pattern in custom_patterns:

        matches = re.findall(
            pattern,
            text
        )

        for match in matches:

            candidate = clean_candidate(
                match
            )

            add_local(
                candidate,
                score_boost
            )

    return local_scores

# =========================
# MAIN LOOP
# =========================
results = []

for post in posts:

    text = post.get(
        "description",
        ""
    )

    transcript = post.get(
        "transcript",
        ""
    )

    # =========================
    # DETECT CITY CONTEXT
    # =========================
    city_context = None

    known_cities = [
        "mississauga",
        "toronto",
        "brampton",
        "vaughan",
        "markham",
        "scarborough",
        "niagara falls"
    ]

    combined_text = (
        text + " " + transcript
    ).lower()

    for city in known_cities:

        if city in combined_text:

            city_context = city.title()
            break

    # =========================
    # CLASSIFY POST
    # =========================
    category = classify_post(text)

    # =========================
    # DESCRIPTION EXTRACTION
    # =========================
    addresses = extract_addresses(text)

    candidate_scores = extract_place_candidates(
        text,
        3
    )

    # =========================
    # TRANSCRIPT FALLBACK
    # =========================
    needs_transcript = (
        (
            not addresses
            or not candidate_scores
        )
        and transcript
    )

    if needs_transcript:

        print("Using transcript fallback...")

        # PLACE CANDIDATES
        transcript_scores = extract_place_candidates(
            transcript,
            2
        )

        for k, v in transcript_scores.items():

            candidate_scores[k] = (
                candidate_scores.get(k, 0)
                + v
            )

    # =========================
    # BUILD PLACE LIST
    # =========================
    sorted_places = sorted(
        candidate_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    place_names = [p[0] for p in sorted_places]

    # =========================
    # REMOVE GENERIC CITY NAMES
    # =========================
    filtered_city_words = {
        "nashville",
        "toronto",
        "mississauga",
        "canada",
        "ontario"
    }

    place_names = [

        p for p in place_names

        if p.lower() not in filtered_city_words
    ]

    # =========================
    # REMOVE SUBSTRING DUPLICATES
    # =========================
    filtered_places = []

    for candidate in place_names:

        is_substring = False

        for existing in filtered_places:

            if candidate.lower() in existing.lower():

                is_substring = True
                break

        if not is_substring:
            filtered_places.append(candidate)

    place_names = filtered_places

    # =========================
    # ENRICH DATA
    # =========================
    enriched_address = None
    enriched_name = None
    latitude = None
    longitude = None

    try:

        location = None

        # --------------------------------
        # PRIORITY 1 → ADDRESS
        # --------------------------------
        if addresses:

            raw_address = addresses[0]

            print(
                "Searching address:",
                raw_address
            )

            search_addresses = [

                raw_address,

                re.sub(
                    r'\s+Unit\s+\w+',
                    '',
                    raw_address,
                    flags=re.IGNORECASE
                ),

                re.sub(
                    r'[A-Z]\d[A-Z]\s?\d[A-Z]\d',
                    '',
                    raw_address,
                    flags=re.IGNORECASE
                )
            ]

            # REMOVE DUPLICATES
            search_addresses = list(
                dict.fromkeys(search_addresses)
            )

            for addr in search_addresses:

                print(
                    "Trying:",
                    addr
                )

                location = geocode(
                    addr,
                    addressdetails=True
                )

                if location:
                    break

            if location:

                enriched_address = (
                    location.address
                )

                latitude = (
                    location.latitude
                )

                longitude = (
                    location.longitude
                )

                if place_names:

                    enriched_name = (
                        place_names[0]
                    )

                else:

                    enriched_name = (
                        location.raw.get(
                            "display_name",
                            ""
                        ).split(",")[0]
                    )

        # --------------------------------
        # PRIORITY 2 → PLACE NAMES
        # --------------------------------
        if not location and place_names:

            for raw_name in place_names:

                cleaned_name = re.sub(
                    r'(?i)\b(explore|visit|must|best|the|place|to|be)\b',
                    '',
                    raw_name
                )

                cleaned_name = re.sub(
                    r'\s+',
                    ' ',
                    cleaned_name
                ).strip()

                search_queries = []

                if city_context:

                    search_queries.append(
                        f"{cleaned_name}, {city_context}, Ontario"
                    )

                search_queries.extend([

                    cleaned_name + ", Ontario, Canada",

                    cleaned_name + ", Toronto, Ontario",

                    cleaned_name
                ])

                for query in search_queries:

                    print(
                        "Searching place:",
                        query
                    )

                    location = geocode(
                        query,
                        addressdetails=True
                    )

                    if location:

                        enriched_address = (
                            location.address
                        )

                        enriched_name = (
                            location.raw.get("name")
                            or raw_name
                        )

                        latitude = (
                            location.latitude
                        )

                        longitude = (
                            location.longitude
                        )

                        break

                if location:
                    break

            # =========================
            # FALLBACK → CITY ONLY
            # =========================
            if not location and city_context:

                city_query = (
                    f"{city_context}, Ontario, Canada"
                )

                print(
                    "Falling back to city:",
                    city_query
                )

                location = geocode(
                    city_query,
                    addressdetails=True
                )

                if location:

                    enriched_address = (
                        location.address
                    )

                    latitude = (
                        location.latitude
                    )

                    longitude = (
                        location.longitude
                    )

                    if place_names:

                        enriched_name = place_names[0]

    except GeocoderTimedOut:

        print("Geocoder timeout.")

    # =========================
    # FINAL RESULT
    # =========================
    result = {

        "tiktok_id": post.get("id"),

        "tiktok_url": post.get("url"),

        "detected_city": city_context,

        "original_text": text,

        "category": category,

        "place_names": place_names,

        "addresses": addresses,

        "enriched_address": enriched_address,

        "enriched_place_name": enriched_name,

        "latitude": latitude,

        "longitude": longitude
    }

    results.append(result)

# =========================
# SAVE RESULTS
# =========================
with open(
    "backend/data/extracted_places.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=4,
        ensure_ascii=False
    )

print("Done!")
print("Saved", len(results), "results.")