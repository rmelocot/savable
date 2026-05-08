from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio
import json

import os

# LIST OF TIKTOK URLS
BASE_DIR = os.path.dirname(__file__)

URL_FILE = os.path.join(
    BASE_DIR,
    "../data/urls.txt"
)

SCRAPED_FILE = os.path.join(
    BASE_DIR,
    "../data/tiktok_posts.json"
)

with open(URL_FILE, "r", encoding="utf-8") as f:
    urls = [
        line.strip()
        for line in f.readlines()
        if line.strip()
    ]

existing_posts = []
existing_urls = set()

if os.path.exists(SCRAPED_FILE):

    with open(SCRAPED_FILE, "r", encoding="utf-8") as f:
        existing_posts = json.load(f)

    existing_urls = {
        post["url"]
        for post in existing_posts
    }

new_urls = [
    url for url in urls
    if url not in existing_urls
]

print("New URLs found:", len(new_urls))
if not new_urls:
    print("No new URLs to scrape.")
    exit()

async def scrape_post(browser, url):

    page = await browser.new_page()
    print("\nOpening:", url)

    await page.goto(url)

    await page.wait_for_timeout(5000)

    html = await page.content()

    soup = BeautifulSoup(html, "html.parser")

    script = soup.find(
        "script",
        {"id": "__UNIVERSAL_DATA_FOR_REHYDRATION__"}
    )

    if not script:
        print("JSON script not found")
        return None

    data = json.loads(script.string)

    default_scope = data["__DEFAULT_SCOPE__"]

    # DETECT POST TYPE
    if "webapp.video-detail" in default_scope:

        print("VIDEO POST")

        post_data = default_scope["webapp.video-detail"]

        post_type = "video"

    elif "webapp.photo-detail" in default_scope:

        print("PHOTO POST")

        post_data = default_scope["webapp.photo-detail"]

        post_type = "photo"

    else:
        print("Unknown post type")
        return None

    item = post_data["itemInfo"]["itemStruct"]
    print(item["video"].keys())

    # =========================
    # EXTRACT TRANSCRIPT
    # =========================
    transcript_text = ""

    subtitle_infos = item.get(
        "video",
        {}
    ).get(
        "subtitleInfos",
        []
    )

    if subtitle_infos:

        try:

            subtitle_url = subtitle_infos[0].get("Url")

            if subtitle_url:

                response = await page.context.request.get(
                    subtitle_url
                )

                subtitle_raw = await response.text()

                try:

                    subtitle_json = json.loads(subtitle_raw)

                    lines = []

                    # TikTok subtitle structure
                    for cue in subtitle_json.get(
                        "utterances",
                        []
                    ):

                        text_part = cue.get("text")

                        if text_part:
                            lines.append(text_part)

                    transcript_text = " ".join(lines)

                except Exception as e:

                    print("Subtitle parse failed:", e)

                    transcript_text = subtitle_raw

        except Exception as e:

            print("Subtitle extraction failed:", e)

    # EXTRACT HASHTAGS
    hashtags = []

    if "textExtra" in item:

        for tag in item["textExtra"]:

            if tag.get("hashtagName"):
                hashtags.append(tag["hashtagName"])

    # CREATE DICTIONARY
    post_info = {

        "type": post_type,

        "id": item["id"],

        "url": url,

        "description": item["desc"],

        "transcript": transcript_text,

        "create_time": item["createTime"],

        "stats": {
            "likes": item["stats"]["diggCount"],
            "comments": item["stats"]["commentCount"],
            "shares": item["stats"]["shareCount"],
            "views": item["stats"]["playCount"]
        },

        "author": {
            "username": item["author"]["uniqueId"],
            "nickname": item["author"]["nickname"],
            "verified": item["author"]["verified"]
        },

        "hashtags": hashtags,

        "music": {
            "title": item["music"]["title"],
            "artist": item["music"]["authorName"]
        }
    }
    await page.close()
    return post_info

async def main():

    all_posts = []

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100
        )

        tasks = [
            scrape_post(browser, url)
            for url in new_urls
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        for result in results:

            if isinstance(result, Exception):

                print("ERROR:", result)

            elif result:

                all_posts.append(result)

        # SAVE ALL POSTS
        existing_posts.extend(all_posts)

        with open(SCRAPED_FILE, "w", encoding="utf-8") as f:
            json.dump(
                existing_posts,
                f,
                indent=4,
                ensure_ascii=False
            )

        print("\nSaved", len(all_posts), "posts!")

        input("\nPress Enter to close browser...")

        await browser.close()

asyncio.run(main())