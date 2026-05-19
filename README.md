# Keepr

A full-stack web app for saving, organizing, and mapping TikTok and Instagram location recommendations in one place.

---

## The Problem

Me and my friends are constantly sending each other places to visit, food spots, and events over DMs. The problem is that as the conversation keeps going, those posts get buried and lost. Saving them natively doesn't really fix it either. TikTok collections and Instagram saved folders are hard to filter through, and there's no way to quickly see everything on a map. On top of that, I'd sometimes forget which platform I saved something on and waste time searching Instagram for a post that was actually on TikTok.

I wanted one place to save TikTok and Instagram posts together, organize them into my own folders, and actually be able to find them on a map, filtered by category, without digging through two separate apps.

---

## How It Works

Paste a TikTok or Instagram post URL. The backend will scrape the post using Playwright, extract the place name with NLP, and geocodes it to a real address and coordinates. The post gets pinned on a map and dropped into whatever folder you choose. 

The goal is to eventually remove the copy-paste step entirely. The plan is a mobile share extension so you can send posts directly from TikTok or Instagram: share button -> More -> Keepr on TikTok, or share > Share to > Keepr on Instagram.

---

## Features

- Interactive map with all saved posts marked at their locations
- Filter by folders (ex. Favourites, Food, Nature, Hackathon, etc.)
- Create custom folders with an accent colour (used for pin on the map)
- Embedded post viewer so you never need to leave the app
- Ability to edit the scraped name or address
- Add star ratings, personal notes, and your own photos per post

---

## Tech Stack

**Frontend**

![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

**Backend**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)

---

## Running Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your system

> On Windows, install Tesseract from [here](https://github.com/UB-Mannheim/tesseract/wiki) and make sure the path in `extract_places.py` matches your install location.

### 1. Clone the repo

```bash
git clone https://github.com/rmelocot/Keepr.git
cd Keepr
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
python -m spacy download en_core_web_sm
python api.py
```

### 3. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will be running at `http://localhost:5173`. The backend runs on `http://localhost:5050`.

> A live demo is coming soon.

---

## License

MIT
