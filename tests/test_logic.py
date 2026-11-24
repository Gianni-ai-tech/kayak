"""Tests de la logique pure (sans réseau ni AWS)."""
import pandas as pd

from kayak.booking import parse_review_score
from kayak.etl import clean_hotels, enrich
from kayak.maps import top_destinations, top_hotels
from kayak.weather import add_weather_score, summarize_forecast


def test_summarize_forecast_sums_rain_averages_rest_skips_none():
    out = summarize_forecast({"daily": {
        "temperature_2m_max": [10, 20, None],
        "precipitation_sum": [1.5, 0, None],
        "precipitation_probability_max": [20, 60, None],
        "cloud_cover_mean": [0, 100, None],
    }})
    assert out == {"temp_max_mean": 15, "rain_mm_total": 1.5, "rain_proba_mean": 40, "clouds_mean": 50}


def test_weather_score_prefers_warm_dry_clear():
    df = pd.DataFrame({
        "city": ["Soleil", "Pluie"],
        "temp_max_mean": [20, 10], "rain_mm_total": [0, 30], "clouds_mean": [10, 90],
    })
    scored = add_weather_score(df)
    assert scored.loc[0, "weather_score"] > scored.loc[1, "weather_score"]


def test_parse_review_score():
    assert parse_review_score("Scored 8.0\n8.0\nVery good\n2,192 reviews") == (8.0, 2192)
    assert parse_review_score("Scored 9.5\n9.5\nExceptional\n1 review") == (9.5, 1)
    assert parse_review_score(None) == (None, None)


def hotels_raw():
    return pd.DataFrame({
        "city_id": [1, 1, 1, 2],
        "city": ["A", "A", "A", "B"],
        "name": ["H1", "H1", "H2", "H3"],
        "url": ["u1", "u1", "u2", "u3"],
        "score": ["8.5", "8.5", None, "9.1"],
        "n_reviews": [10, 10, None, 5],
        "lat": [45.0, 45.0, None, 43.0],
        "lon": [6.0, 6.0, None, 5.0],
        "description": [" desc ", " desc ", None, "d3"],
    })


def test_clean_hotels_dedupes_and_drops_missing_coords():
    out = clean_hotels(hotels_raw())
    assert list(out["name"]) == ["H1", "H3"]
    assert list(out["hotel_id"]) == [1, 2]
    assert out["score"].dtype.kind == "f"
    assert out.loc[0, "description"] == "desc"


def test_enrich_adds_city_weather_to_each_hotel():
    cities = pd.DataFrame({"city_id": [1, 2], "city": ["A", "B"], "lat": [0, 0], "lon": [0, 0],
                           "weather_score": [0.9, 0.1]})
    out = enrich(clean_hotels(hotels_raw()), cities)
    assert list(out["city_weather_score"]) == [0.9, 0.1]


def test_top_hotels_only_in_top_cities():
    cities = pd.DataFrame({"city_id": [1, 2, 3], "weather_score": [0.2, 0.9, 0.5]})
    hotels = pd.DataFrame({"city_id": [1, 2, 3, 2, 3],
                           "score": [9.9, 8.0, 7.0, 9.0, 9.8],
                           "n_reviews": [500, 500, 500, 500, 3]})
    best = top_destinations(cities, n=2)
    assert list(best["city_id"]) == [2, 3]
    # 9.9 hors top villes, 9.8 avec 3 avis seulement : tous deux écartés
    assert list(top_hotels(hotels, best["city_id"], n=2)["score"]) == [9.0, 8.0]
