import sys

URL_FILE = "data/urls.txt"

url = sys.argv[1]

with open(URL_FILE, "a", encoding="utf-8") as f:
    f.write(url + "\n")

print("Added URL:", url)