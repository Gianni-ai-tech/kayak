"""Étape 2 : scraping Booking.com (nom, URL, coordonnées, note, description) pour chaque ville.

Playwright (vrai navigateur) car Booking renvoie un challenge JavaScript aux clients HTTP simples.
Reprise automatique : les villes déjà présentes dans data/hotels.csv sont sautées.

Sortie : data/hotels.csv
Lancer : python -m kayak.booking
"""
import re
import time
from urllib.parse import quote_plus

import pandas as pd
from playwright.sync_api import Page, sync_playwright

from kayak.config import CITIES, DATA_DIR, HEADLESS, HOTELS_CSV, HOTELS_PER_CITY


def parse_review_score(text: str | None) -> tuple[float | None, int | None]:
    """'Scored 8.0\\n8.0\\nVery good\\n2,192 reviews' -> (8.0, 2192)."""
    if not text:
        return None, None
    score = re.search(r"\d+(?:\.\d+)?", text)
    reviews = re.search(r"([\d,]+)\s+reviews?", text)
    return (float(score.group()) if score else None,
            int(reviews.group(1).replace(",", "")) if reviews else None)


def search_hotels(page: Page, city: str, n: int) -> list[dict]:
    """Nom, URL, note des n premiers hôtels de la page de résultats."""
    page.goto(f"https://www.booking.com/searchresults.en-gb.html?ss={quote_plus(city + ', France')}&lang=en-gb")
    page.wait_for_selector('[data-testid="property-card"]', timeout=30_000)
    reject = page.locator("#onetrust-reject-all-handler")  # bandeau cookies : refus
    if reject.count():
        reject.click()
    hotels = []
    for card in page.locator('[data-testid="property-card"]').all()[:n]:
        link = card.locator('a[data-testid="title-link"]').first.get_attribute("href") or ""
        score_el = card.locator('[data-testid="review-score"]')
        score, n_reviews = parse_review_score(score_el.first.inner_text() if score_el.count() else None)
        hotels.append({
            "name": card.locator('[data-testid="title"]').first.inner_text().strip(),
            "url": link.split("?")[0],
            "score": score,
            "n_reviews": n_reviews,
        })
    return hotels


def hotel_details(page: Page, url: str) -> dict:
    """Coordonnées et description depuis la fiche de l'hôtel."""
    page.goto(url)
    page.wait_for_selector('[data-testid="property-description"]', timeout=30_000)
    latlng = page.locator("[data-atlas-latlng]").first.get_attribute("data-atlas-latlng") or ","
    lat, lon = (latlng.split(",") + ["", ""])[:2]
    return {
        "lat": float(lat) if lat else None,
        "lon": float(lon) if lon else None,
        "description": page.locator('[data-testid="property-description"]').first.inner_text().strip(),
    }


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    done = set(pd.read_csv(HOTELS_CSV)["city_id"]) if HOTELS_CSV.exists() else set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page(locale="en-GB")
        for city_id, city in enumerate(CITIES, start=1):
            if city_id in done:
                continue
            rows = []
            for h in search_hotels(page, city, HOTELS_PER_CITY):
                try:
                    h.update(hotel_details(page, h["url"]))
                except Exception as e:  # une fiche qui ne charge pas ne bloque pas la ville
                    print(f"   fiche ignorée ({e.__class__.__name__}) : {h['url']}")
                rows.append({"city_id": city_id, "city": city, **h})
                time.sleep(1.5)  # rester raisonnable avec le site
            pd.DataFrame(rows).to_csv(HOTELS_CSV, mode="a", header=not HOTELS_CSV.exists(), index=False)
            print(f"{city_id:>2} {city}: {len(rows)} hôtels")
        browser.close()
    print(f"-> {HOTELS_CSV}")


if __name__ == "__main__":
    main()
