"""Étape 1 : coordonnées GPS (Photon / OpenStreetMap) + prévisions météo 7 jours (Open-Meteo) + score par ville.

Sortie : data/cities_weather.csv
Lancer : python -m kayak.weather
"""
import time

import pandas as pd
import requests

from kayak.config import CITIES, CITIES_CSV, DATA_DIR

HEADERS = {"User-Agent": "jedha-kayak-project (student)"}
DAILY = "temperature_2m_max,precipitation_sum,precipitation_probability_max,cloud_cover_mean"


def geocode(city: str) -> tuple[float, float]:
    """Latitude/longitude via Photon (géocodeur OpenStreetMap, comme Nominatim,
    mais sans le blocage 429 rencontré sur Nominatim au-delà de ~1 requête/s)."""
    query = {"St Malo": "Saint-Malo"}.get(city, city)  # "St Malo" seul tombe sur un lieu-dit des Pyrénées-Orientales
    r = requests.get(
        "https://photon.komoot.io/api/",
        params={"q": f"{query}, France", "limit": 1},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    lon, lat = r.json()["features"][0]["geometry"]["coordinates"]
    return float(lat), float(lon)


def fetch_forecast(lat: float, lon: float) -> dict:
    """Prévisions journalières sur 7 jours (Open-Meteo : gratuit, sans clé)."""
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "daily": DAILY,
                "forecast_days": 7, "timezone": "Europe/Paris"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def summarize_forecast(forecast: dict) -> dict:
    """Agrège les 7 jours en quelques indicateurs (valeurs manquantes ignorées)."""
    d = forecast["daily"]

    def vals(key):
        return [v for v in d[key] if v is not None]

    return {
        "temp_max_mean": sum(vals("temperature_2m_max")) / len(vals("temperature_2m_max")),
        "rain_mm_total": sum(vals("precipitation_sum")),
        "rain_proba_mean": sum(vals("precipitation_probability_max")) / len(vals("precipitation_probability_max")),
        "clouds_mean": sum(vals("cloud_cover_mean")) / len(vals("cloud_cover_mean")),
    }


def add_weather_score(df: pd.DataFrame) -> pd.DataFrame:
    """Score 0-1 : moyenne de 3 rangs (chaud = mieux, peu de pluie = mieux, peu de nuages = mieux)."""
    df = df.copy()
    df["weather_score"] = (
        df["temp_max_mean"].rank(pct=True)
        + (-df["rain_mm_total"]).rank(pct=True)
        + (-df["clouds_mean"]).rank(pct=True)
    ) / 3
    return df


def build(raw: list[dict]) -> pd.DataFrame:
    """raw : [{city_id, city, lat, lon, forecast}] -> table des villes scorées."""
    rows = [{"city_id": r["city_id"], "city": r["city"], "lat": r["lat"], "lon": r["lon"],
             **summarize_forecast(r["forecast"])} for r in raw]
    df = add_weather_score(pd.DataFrame(rows))
    df["forecast_date"] = pd.Timestamp.now().normalize()
    return df


def main(raw_json: str | None = None) -> None:
    """Sans argument : interroge les API. Avec un JSON brut déjà collecté (même structure) : le rejoue."""
    if raw_json:
        import json
        with open(raw_json, encoding="utf-8") as f:
            _write(build(json.load(f)))
        return
    raw = []
    for city_id, city in enumerate(CITIES, start=1):
        lat, lon = geocode(city)
        time.sleep(1)  # rester raisonnable avec le service gratuit
        raw.append({"city_id": city_id, "city": city, "lat": lat, "lon": lon,
                    "forecast": fetch_forecast(lat, lon)})
        print(f"{city_id:>2} {city}: ok")
    _write(build(raw))


def _write(df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(CITIES_CSV, index=False)
    print(f"-> {CITIES_CSV}")
    print(df.sort_values("weather_score", ascending=False)[["city", "weather_score"]].head(5))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
