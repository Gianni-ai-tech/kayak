"""Étape 4 : ETL  S3 (raw/) -> nettoyage -> S3 (processed/) + RDS (data warehouse).

Tables créées : cities, hotels (hotels.city_id -> cities.city_id).
Lancer : python -m kayak.etl
"""
import io

import boto3
import pandas as pd
from sqlalchemy import create_engine

from kayak.config import DATA_DIR, DB_URL, ENRICHED_CSV, S3_BUCKET


def clean_cities(df: pd.DataFrame) -> pd.DataFrame:
    return (df.drop_duplicates("city_id")
              .dropna(subset=["lat", "lon", "weather_score"])
              .reset_index(drop=True))


def clean_hotels(df: pd.DataFrame) -> pd.DataFrame:
    """Dédoublonne (même hôtel trouvé deux fois pour une ville), types numériques, coordonnées obligatoires."""
    df = df.drop_duplicates(["city_id", "url"]).copy()
    for col in ("score", "lat", "lon", "n_reviews"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    df["description"] = df["description"].fillna("").str.strip()
    df.insert(0, "hotel_id", range(1, len(df) + 1))
    return df.reset_index(drop=True)


def enrich(hotels: pd.DataFrame, cities: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par hôtel avec la météo de sa ville : le CSV enrichi demandé dans les livrables."""
    weather = cities.drop(columns=["city", "lat", "lon"]).rename(columns=lambda c: c if c == "city_id" else f"city_{c}")
    return hotels.merge(weather, on="city_id", how="inner")


def read_s3_csv(s3, key: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(s3.get_object(Bucket=S3_BUCKET, Key=key)["Body"].read()))


def main() -> None:
    if not (S3_BUCKET and DB_URL):
        raise SystemExit("S3_BUCKET et DB_URL requis dans .env")
    s3 = boto3.client("s3")
    cities = clean_cities(read_s3_csv(s3, "raw/cities_weather.csv"))
    hotels = clean_hotels(read_s3_csv(s3, "raw/hotels.csv"))
    enriched = enrich(hotels, cities)

    DATA_DIR.mkdir(exist_ok=True)
    enriched.to_csv(ENRICHED_CSV, index=False)
    s3.upload_file(str(ENRICHED_CSV), S3_BUCKET, f"processed/{ENRICHED_CSV.name}")
    print(f"-> s3://{S3_BUCKET}/processed/{ENRICHED_CSV.name}")

    engine = create_engine(DB_URL)
    with engine.begin() as conn:  # une transaction : tout est rechargé, ou rien
        conn.exec_driver_sql("DROP TABLE IF EXISTS hotels; DROP TABLE IF EXISTS cities;")
        cities.to_sql("cities", conn, index=False)
        hotels.to_sql("hotels", conn, index=False)
        conn.exec_driver_sql(
            "ALTER TABLE cities ADD PRIMARY KEY (city_id);"
            "ALTER TABLE hotels ADD PRIMARY KEY (hotel_id);"
            "ALTER TABLE hotels ADD FOREIGN KEY (city_id) REFERENCES cities (city_id);"
        )
    print(f"-> RDS : cities ({len(cities)} lignes), hotels ({len(hotels)} lignes), clés posées")


if __name__ == "__main__":
    main()
