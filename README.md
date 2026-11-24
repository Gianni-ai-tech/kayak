# Kayak – Plan your trip (Jedha CDSD, bloc 1)

Recommander les meilleures destinations françaises (météo des 7 prochains jours) et leurs meilleurs hôtels, à partir de données réelles collectées, stockées dans un data lake S3, puis chargées dans un data warehouse RDS PostgreSQL.

## Architecture

```
Photon/OSM (GPS) ─┐
Open-Meteo (7 j) ─┴─> data/cities_weather.csv ─┐
Booking.com ────────> data/hotels.csv ─────────┴─> S3 raw/ ──ETL──> S3 processed/hotels_enriched.csv
                                                                └──> RDS PostgreSQL (cities 1-n hotels) ──> cartes plotly
```

| Étape | Code | Sortie |
|---|---|---|
| 1. GPS + météo + score | `kayak/weather.py` | `data/cities_weather.csv` |
| 2. Scraping Booking | `kayak/booking.py` (Playwright) / `scripts/booking_in_browser.js` | `data/hotels.csv` |
| 3. Data lake | `kayak/datalake.py` | `s3://<bucket>/raw/*.csv` |
| 4. ETL | `kayak/etl.py` | `s3://<bucket>/processed/hotels_enriched.csv` + tables RDS `cities`, `hotels` |
| 5. Cartes | `kayak/maps.py` | `maps/top5_destinations.html`, `maps/top20_hotels.html` |

## Choix techniques
- **Météo : Open-Meteo**, gratuit et sans clé, prévisions journalières sur 7 jours. One Call 3.0 d'OpenWeather, citée dans l'énoncé, exige maintenant une carte bancaire, et l'API gratuite d'OpenWeather s'arrête à 5 jours.
- **Géocodage : Photon** (OpenStreetMap). Nominatim renvoyait des erreurs 429 (trop de requêtes) au-delà d'environ 1 requête/s. « St Malo » seul tombe sur un lieu-dit des Pyrénées-Orientales, d'où la requête « Saint-Malo ».
- **Score météo** : moyenne de trois rangs percentiles (température max ↑, pluie cumulée ↓, nuages ↓). Simple, explicable, sans pondération arbitraire.
- **Scraping** : Booking renvoie un challenge JavaScript aux clients HTTP simples. Le jeu livré a été collecté avec `scripts/booking_in_browser.js`, exécuté dans un onglet booking.com : `fetch` same-origin + `DOMParser`, 1 s entre deux pages. `kayak/booking.py` fait la même chose avec Playwright, pour rejouer en ligne de commande.
- **Infrastructure** : S3 et RDS PostgreSQL (`db.t4g.micro`, une seule zone, 20 Go) en `eu-west-3`. L'ETL tourne dans AWS CloudShell. Le groupe de sécurité n'ouvre le port 5432 qu'à l'IP de CloudShell.
- **Modèle** : `cities(city_id PK, …)` 1-n `hotels(hotel_id PK, city_id FK, …)`.

## Rejouer
```bash
pip install -r requirements.txt
pytest                                   # logique testée sans réseau
python -m kayak.weather                  # ou : python -m kayak.weather data/kayak_weather_raw.json
python -m kayak.booking                  # playwright install chromium au préalable
python -m kayak.datalake                 # .env : S3_BUCKET
python -m kayak.etl                      # .env : S3_BUCKET, DB_URL
python -m kayak.maps
```

## Nettoyage après la soutenance
```bash
aws rds delete-db-instance --db-instance-identifier kayak-db --skip-final-snapshot --region eu-west-3
```
