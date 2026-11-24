"""Configuration commune : villes du périmètre, chemins, variables d'environnement."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MAPS_DIR = ROOT / "maps"

CITIES_CSV = DATA_DIR / "cities_weather.csv"
HOTELS_CSV = DATA_DIR / "hotels.csv"
ENRICHED_CSV = DATA_DIR / "hotels_enriched.csv"

# Top-35 imposé par l'énoncé Jedha (l'ordre fixe l'id de chaque ville).
CITIES = [
    "Mont Saint Michel", "St Malo", "Bayeux", "Le Havre", "Rouen", "Paris",
    "Amiens", "Lille", "Strasbourg", "Chateau du Haut Koenigsbourg", "Colmar",
    "Eguisheim", "Besancon", "Dijon", "Annecy", "Grenoble", "Lyon",
    "Gorges du Verdon", "Bormes les Mimosas", "Cassis", "Marseille",
    "Aix en Provence", "Avignon", "Uzes", "Nimes", "Aigues Mortes",
    "Saintes Maries de la mer", "Collioure", "Carcassonne", "Ariege",
    "Toulouse", "Montauban", "Biarritz", "Bayonne", "La Rochelle",
]

OWM_API_KEY = os.getenv("OWM_API_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
DB_URL = os.getenv("DB_URL", "")  # ex : postgresql+psycopg2://user:pwd@host:5432/kayak
HOTELS_PER_CITY = int(os.getenv("HOTELS_PER_CITY", "20"))
HEADLESS = os.getenv("HEADLESS", "0") == "1"
