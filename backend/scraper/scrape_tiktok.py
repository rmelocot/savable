from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio
import json
import os
import re
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
URL_FILE      = os.path.join(BASE_DIR, "../data/urls.txt")
SCRAPED_FILE  = os.path.join(BASE_DIR, "../data/tiktok_posts.json")
THUMBS_DIR    = os.path.join(BASE_DIR, "../data/thumbnails")


def normalise_url(url):
    # Strip query params and trailing slashes so URLs can be compared consistently
    url = url.split("?")[0].rstrip("/")
    url = url.replace("/photo/", "/video/")
    return url


def download_thumbnail(url: str, post_id: str) -> str | None:
    """
    Download a thumbnail from a remote URL and save it locally so it never expires.
    Returns the relative local path, or None if the download fails.
    """
    if not url:
        return None
    os.makedirs(THUMBS_DIR, exist_ok=True)
    ext = ".jpg"
    local_path = os.path.join(THUMBS_DIR, f"{post_id}{ext}")
    # Skip the download if we already have it saved
    if os.path.exists(local_path):
        return f"thumbnails/{post_id}{ext}"
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(response.content)
        print(f"  Thumbnail saved: {local_path}")
        return f"thumbnails/{post_id}{ext}"
    except Exception as e:
        print(f"  Thumbnail download failed: {e}")
        return None


async def get_tiktok_data(page, url, retries=3):
    for attempt in range(retries):
        await page.goto(url)
        await page.wait_for_timeout(5000 + attempt * 3000)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", {"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
        if not script:
            print(f"  TikTok: JSON script not found (attempt {attempt + 1})")
            continue

        data = json.loads(script.string)
        default_scope = data.get("__DEFAULT_SCOPE__", {})
        keys = list(default_scope.keys())
        print(f"  Scope keys: {keys}")

        if "webapp.video-detail" in default_scope:
            return default_scope["webapp.video-detail"], "video"
        elif "webapp.photo-detail" in default_scope:
            return default_scope["webapp.photo-detail"], "photo"
        else:
            # The page may not have fully loaded yet — scroll to trigger lazy rendering and retry
            print(f"  TikTok: post data not in scope yet (attempt {attempt + 1}), retrying...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            script = soup.find("script", {"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"})
            if script:
                data = json.loads(script.string)
                default_scope = data.get("__DEFAULT_SCOPE__", {})
                if "webapp.video-detail" in default_scope:
                    return default_scope["webapp.video-detail"], "video"
                elif "webapp.photo-detail" in default_scope:
                    return default_scope["webapp.photo-detail"], "photo"

    return None, None


async def scrape_tiktok(page, url, forced_type=None):
    post_data, post_type = await get_tiktok_data(page, url)
    if not post_data:
        print("  TikTok: could not get post data after retries")
        return None

    if forced_type:
        post_type = forced_type

    print(f"  TikTok: {post_type.upper()} POST")
    item = post_data["itemInfo"]["itemStruct"]

    transcript_text = ""
    if post_type == "video":
        subtitle_infos = item.get("video", {}).get("subtitleInfos", [])
        if subtitle_infos:
            try:
                subtitle_url = subtitle_infos[0].get("Url")
                if subtitle_url:
                    response = await page.context.request.get(subtitle_url)
                    subtitle_raw = await response.text()
                    try:
                        # TikTok subtitles are sometimes JSON, sometimes raw VTT
                        subtitle_json = json.loads(subtitle_raw)
                        lines = [cue.get("text") for cue in subtitle_json.get("utterances", []) if cue.get("text")]
                        transcript_text = " ".join(lines)
                    except Exception as e:
                        print("  Subtitle parse failed:", e)
                        transcript_text = subtitle_raw
            except Exception as e:
                print("  Subtitle extraction failed:", e)

    hashtags = [tag["hashtagName"] for tag in item.get("textExtra", []) if tag.get("hashtagName")]

    # Extract the point-of-interest tag if the creator tagged a location
    poi_data = None
    raw_poi = item.get("poi")
    if raw_poi:
        poi_name    = raw_poi.get("name", "").strip()
        poi_address = raw_poi.get("address", "").strip()
        if poi_name or poi_address:
            poi_data = {"name": poi_name, "address": poi_address}
            print(f"  POI found: {poi_data}")

    display_url = url.replace("/video/", "/photo/") if post_type == "photo" else url

    return {
        "platform":    "tiktok",
        "type":        post_type,
        "id":          item["id"],
        "url":         display_url,
        "description": item["desc"],
        "transcript":  transcript_text,
        "create_time": item["createTime"],
        "stats": {
            "likes":    item["stats"]["diggCount"],
            "comments": item["stats"]["commentCount"],
            "shares":   item["stats"]["shareCount"],
            "views":    item["stats"]["playCount"],
        },
        "author": {
            "username": item["author"]["uniqueId"],
            "nickname": item["author"]["nickname"],
            "verified": item["author"]["verified"],
        },
        "hashtags": hashtags,
        "music": {
            "title":  item["music"]["title"],
            "artist": item["music"]["authorName"],
        },
        "poi": poi_data,
    }


async def scrape_instagram(page, url):
    clean_url  = normalise_url(url)
    oembed_url = f"https://www.instagram.com/api/v1/oembed/?url={clean_url}"

    await page.goto(oembed_url)
    await page.wait_for_timeout(3000)

    try:
        body   = await page.inner_text("body")
        oembed = json.loads(body)
    except Exception as e:
        print("  Instagram oEmbed failed:", e)
        oembed = {}

    await page.goto(clean_url)
    await page.wait_for_timeout(5000)

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    caption = ""
    og_desc = soup.find("meta", {"property": "og:description"})
    if og_desc:
        caption = og_desc.get("content", "")

    # CDN thumbnail URLs expire, so we download and store them locally
    remote_thumbnail = oembed.get("thumbnail_url", "")
    if not remote_thumbnail:
        og_img = soup.find("meta", {"property": "og:image"})
        if og_img:
            remote_thumbnail = og_img.get("content", "")

    hashtags    = re.findall(r"#(\w+)", caption)
    author_name = oembed.get("author_name", "")
    author_url  = oembed.get("author_url", "")

    shortcode_match = re.search(r"/p/([^/]+)", clean_url) or re.search(r"/reel/([^/]+)", clean_url)
    post_id = shortcode_match.group(1) if shortcode_match else clean_url

    local_thumbnail = download_thumbnail(remote_thumbnail, post_id)

    print(f"  Instagram: got post {post_id}, thumbnail: {local_thumbnail or 'none'}")

    return {
        "platform":          "instagram",
        "type":              "instagram",
        "id":                post_id,
        "url":               clean_url,
        "description":       caption,
        "transcript":        "",
        "create_time":       "",
        "thumbnail":         local_thumbnail,
        "thumbnail_remote":  remote_thumbnail,
        "stats":             {"likes": None, "comments": None, "shares": None, "views": None},
        "author":            {"username": author_name, "nickname": author_name, "verified": False, "profile_url": author_url},
        "hashtags":          hashtags,
        "music":             None,
        "poi":               None,
    }


async def scrape_post(browser, url, forced_type=None):
    # Photo posts use the same underlying data as video posts, just with a different URL segment
    is_photo = "/photo/" in url
    scrape_url = url.replace("/photo/", "/video/") if is_photo else url
    if is_photo and not forced_type:
        forced_type = "photo"

    page = await browser.new_page()
    print("\nOpening:", scrape_url)
    try:
        if "tiktok.com" in scrape_url:
            result = await scrape_tiktok(page, scrape_url, forced_type=forced_type)
            # Restore the original photo URL so it's stored correctly in the output
            if result and is_photo:
                result["url"] = url
        elif "instagram.com" in scrape_url:
            result = await scrape_instagram(page, scrape_url)
        else:
            print("  Unsupported platform:", scrape_url)
            result = None
    except Exception as e:
        print("  ERROR scraping:", e)
        result = None
    finally:
        await page.close()
    return result

async def _main(new_urls, existing_posts):
    all_posts = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=100)
        # Scrape all new URLs concurrently to save time
        results = await asyncio.gather(
            *[scrape_post(browser, url, forced_type=ft) for url, ft in new_urls],
            return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                print("ERROR:", result)
            elif result:
                all_posts.append(result)
        await browser.close()
    return all_posts


def run():
    with open(URL_FILE, "r", encoding="utf-8") as f:
        raw_lines = [line.strip() for line in f if line.strip()]

    all_urls = [(line.strip(), None) for line in raw_lines]

    existing_posts = []
    existing_urls  = set()
    if os.path.exists(SCRAPED_FILE):
        with open(SCRAPED_FILE, "r", encoding="utf-8") as f:
            existing_posts = json.load(f)
        # Build a set of already-scraped URLs so we don't process duplicates
        existing_urls = {normalise_url(post.get("url") or post.get("tiktok_url", "")) for post in existing_posts}

    new_urls = [(url, ft) for url, ft in all_urls if normalise_url(url) not in existing_urls]
    print("New URLs found:", len(new_urls))

    if not new_urls:
        print("No new URLs to scrape.")
        return

    all_posts = asyncio.run(_main(new_urls, existing_posts))
    existing_posts.extend(all_posts)

    with open(SCRAPED_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_posts, f, indent=4, ensure_ascii=False)

    print(f"\nSaved {len(all_posts)} posts!")


if __name__ == "__main__":
    run()