#!/usr/bin/env python3
"""Download product thumbnails for the products slides (fails soft: missing images render as placeholder tiles).
Usage: python3 fetch_thumbs.py <week_start>
Reads products.image_urls ("title|type" -> Shopify featuredMedia URL) from data/raw_<week>.json and saves
4:5 JPEGs to assets/products/<slug>.jpg. Needs network access to cdn.shopify.com."""
import io, json, os, re, sys, urllib.request
from pathlib import Path
from PIL import Image, ImageOps
WORK = Path(os.environ.get("MERCH_WORK") or os.getcwd())  # run folder
def slug(key): return re.sub(r"[^a-z0-9]+", "-", key.replace("|", " ").lower()).strip("-")
def main(week):
    raw = json.loads((WORK / "data" / f"raw_{week}.json").read_text())
    out = WORK / "assets" / "products"; out.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for key, url in raw.get("products", {}).get("image_urls", {}).items():
        dest = out / f"{slug(key)}.jpg"
        if dest.exists(): ok += 1; continue
        try:
            sep = "&" if "?" in url else "?"
            data = urllib.request.urlopen(url + sep + "width=400", timeout=20).read()
            im = ImageOps.fit(Image.open(io.BytesIO(data)).convert("RGB"), (400, 500), centering=(0.5, 0.4))
            im.save(dest, quality=85); ok += 1
        except Exception as e:
            fail += 1; print(f"thumbnail not fetched: {key} ({e.__class__.__name__})")
    print(f"thumbnails: {ok} ready, {fail} missing (placeholders will show)")
if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-09-28")
