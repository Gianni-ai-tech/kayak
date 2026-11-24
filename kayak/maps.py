"""Étape 5 : les deux cartes demandées, lues depuis le data warehouse (RDS).

- maps/top5_destinations.html : 5 villes au meilleur score météo
- maps/top20_hotels.html      : 20 hôtels les mieux notés dans ces 5 villes
Lancer : python -m kayak.maps
"""
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

from kayak.config import DB_URL, MAPS_DIR


def top_destinations(cities: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    return cities.nlargest(n, "weather_score")


def top_hotels(hotels: pd.DataFrame, city_ids, n: int = 20, min_reviews: int = 50) -> pd.DataFrame:
    """Meilleures notes dans les villes retenues ; un 9.8 sur 3 avis n'est pas fiable, d'où le seuil."""
    pool = hotels[hotels["city_id"].isin(city_ids) & (hotels["n_reviews"] >= min_reviews)]
    return pool.sort_values(["score", "n_reviews"], ascending=False).head(n)


def main() -> None:
    engine = create_engine(DB_URL)
    cities = pd.read_sql("SELECT * FROM cities", engine)
    hotels = pd.read_sql("SELECT * FROM hotels", engine)
    top5 = top_destinations(cities)
    top20 = top_hotels(hotels, top5["city_id"])

    MAPS_DIR.mkdir(exist_ok=True)
    fig = px.scatter_map(top5, lat="lat", lon="lon", size="weather_score", color="weather_score",
                         hover_name="city", hover_data=["temp_max_mean", "rain_mm_total", "clouds_mean"],
                         zoom=4.5, title="Top 5 destinations (météo 7 prochains jours)")
    fig.write_html(MAPS_DIR / "top5_destinations.html")
    fig = px.scatter_map(top20, lat="lat", lon="lon", color="score", hover_name="name",
                         hover_data=["city", "score", "n_reviews"], zoom=4.5,
                         title="Top 20 hôtels dans les 5 meilleures destinations")
    fig.write_html(MAPS_DIR / "top20_hotels.html")
    print(f"-> {MAPS_DIR}")
    print(top5[["city", "weather_score"]])


if __name__ == "__main__":
    main()
