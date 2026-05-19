import sys
sys.stdout.reconfigure(line_buffering=True)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import threading
import traceback
import json
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "scraper"))

import scrape_tiktok
import extract_places
import clean_places

# Prevent multiple pipeline runs from overlapping if requests come in quickly
pipeline_lock = threading.Lock()
app = Flask(__name__)
CORS(app)

URL_FILE      = os.path.join(BASE_DIR, "data/urls.txt")
CLEANED_FILE  = os.path.join(BASE_DIR, "data/cleaned_places.json")
SCRAPED_FILE  = os.path.join(BASE_DIR, "data/tiktok_posts.json")
THUMBS_DIR    = os.path.join(BASE_DIR, "data/thumbnails")


# ─── Serve local thumbnails ───────────────────────────────────────────────────

@app.route("/thumbnails/<path:filename>")
def serve_thumbnail(filename):
    return send_from_directory(THUMBS_DIR, filename)


# ─── Backfill missing thumbnails on startup ───────────────────────────────────

def backfill_thumbnails():
    """
    On startup, check for any Instagram posts that have a remote thumbnail URL
    but no locally saved image. Downloads and saves them so they're always available.
    """
    if not os.path.exists(SCRAPED_FILE):
        return
    try:
        with open(SCRAPED_FILE, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except Exception:
        return

    os.makedirs(THUMBS_DIR, exist_ok=True)
    changed = False

    for post in posts:
        if post.get("platform") != "instagram":
            continue

        post_id = post.get("id", "")
        local_path = os.path.join(THUMBS_DIR, f"{post_id}.jpg")
        already_local = (
            post.get("thumbnail", "").startswith("thumbnails/")
            and os.path.exists(local_path)
        )
        if already_local:
            continue

        # Prefer the stored remote URL; fall back to the thumbnail field if it's still a CDN link
        remote_url = post.get("thumbnail_remote") or (
            post.get("thumbnail") if post.get("thumbnail", "").startswith("http") else ""
        )
        if not remote_url:
            continue

        print(f">>> Backfill thumbnail for {post_id}...", flush=True)
        local = scrape_tiktok.download_thumbnail(remote_url, post_id)
        if local:
            post["thumbnail_remote"] = remote_url
            post["thumbnail"] = local
            changed = True

    if changed:
        with open(SCRAPED_FILE, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=4, ensure_ascii=False)
        print(">>> Backfill complete, tiktok_posts.json updated.", flush=True)

        # Re-run the cleaning step so cleaned_places.json reflects the updated local paths
        try:
            clean_places.run()
            print(">>> clean_places re-run after backfill.", flush=True)
        except Exception as e:
            print(f">>> clean_places re-run failed: {e}", flush=True)


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def run_pipeline():
    if not pipeline_lock.acquire(blocking=False):
        print(">>> Pipeline already running, skipping.", flush=True)
        return
    try:
        print(">>> Pipeline: running scraper", flush=True)
        scrape_tiktok.run()
        print(">>> scraper done!", flush=True)

        print(">>> Pipeline: running extract_places", flush=True)
        extract_places.run()
        print(">>> extract done!", flush=True)

        print(">>> Pipeline: running clean_places", flush=True)
        clean_places.run()
        print(">>> Pipeline: all done!", flush=True)

    except Exception as e:
        print(f">>> Pipeline FAILED: {e}", flush=True)
        traceback.print_exc()
    finally:
        pipeline_lock.release()


def pipeline_with_error_logging():
    print(">>> Thread started", flush=True)
    run_pipeline()


def extract_post_id(url: str) -> str | None:
    # Pull the post ID out of TikTok or Instagram URLs regardless of post type
    for segment in ["video", "photo"]:
        if f"/{segment}/" in url:
            return url.split(f"/{segment}/")[1].split("?")[0].rstrip("/")
    for segment in ["reel", "p"]:
        if f"/{segment}/" in url:
            return url.split(f"/{segment}/")[1].split("?")[0].rstrip("/")
    return None


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/add-url", methods=["POST"])
def add_url():
    data = request.get_json()
    url = (data or {}).get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    existing = set()
    if os.path.exists(URL_FILE):
        with open(URL_FILE, "r", encoding="utf-8") as f:
            existing = {line.strip().replace(" #photo", "") for line in f if line.strip()}

    if url in existing:
        return jsonify({"message": "URL already exists"}), 200
    
    with open(URL_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

    # Kick off the scrape pipeline in the background so the response returns immediately
    threading.Thread(target=pipeline_with_error_logging, daemon=True).start()
    return jsonify({"message": "URL added, pipeline started"}), 200


@app.route("/result", methods=["GET"])
def get_result():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    query_id = extract_post_id(url)
    print(f">>> /result queried with id: {query_id}", flush=True)

    if not query_id:
        return jsonify({"error": f"Could not extract post ID from URL: {url}"}), 400

    if not os.path.exists(CLEANED_FILE):
        return jsonify({"error": "No results yet"}), 404

    try:
        with open(CLEANED_FILE, "r", encoding="utf-8") as f:
            places = json.load(f)
    except Exception as e:
        return jsonify({"error": "Could not read results"}), 500

    thumbnails = {}
    if os.path.exists(SCRAPED_FILE):
        try:
            with open(SCRAPED_FILE, "r", encoding="utf-8") as f:
                raw_posts = json.load(f)
            for p in raw_posts:
                pid = p.get("id") or extract_post_id(p.get("url", ""))
                if pid:
                    thumbnails[pid] = p.get("thumbnail", "")
        except Exception:
            pass

    for place in places:
        stored_url = place.get("tiktok_url") or ""
        stored_id  = place.get("tiktok_id") or extract_post_id(stored_url)
        if query_id and stored_id and query_id == stored_id:
            thumb = thumbnails.get(stored_id, "")
            # Convert the local relative path to a full URL the frontend can load
            if thumb and thumb.startswith("thumbnails/"):
                thumb = f"http://localhost:5050/{thumb}"
            return jsonify({
                "found":      True,
                "name":       place.get("name"),
                "address":    place.get("address"),
                "latitude":   place.get("latitude"),
                "longitude":  place.get("longitude"),
                "category":   place.get("category"),
                "tiktok_url": place.get("tiktok_url"),
                "thumbnail":  thumb,
            }), 200

    return jsonify({"found": False}), 404


# ─── Startup ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Kick off thumbnail backfill in the background so startup isn't delayed
    threading.Thread(target=backfill_thumbnails, daemon=True).start()
    app.run(port=5050, debug=True, use_reloader=False)