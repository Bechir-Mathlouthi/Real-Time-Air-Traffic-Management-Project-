import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "flights.db"

# OpenSky Network API settings
OPENSKY_USERNAME = os.getenv("OPENSKY_USERNAME")
OPENSKY_PASSWORD = os.getenv("OPENSKY_PASSWORD")
OPENSKY_API_BASE = "https://opensky-network.org/api"

# Region settings
REGION_BOUNDS = [
    float(os.getenv("MIN_LATITUDE", "41.0")),  # min latitude
    float(os.getenv("MAX_LATITUDE", "51.0")),  # max latitude
    float(os.getenv("MIN_LONGITUDE", "-5.0")), # min longitude
    float(os.getenv("MAX_LONGITUDE", "9.0"))   # max longitude
]

# Model settings
MODEL_PATH = MODELS_DIR / "delay_prediction_model.pkl"

# Dashboard settings
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "60"))  # seconds
MAP_CENTER = [(REGION_BOUNDS[0] + REGION_BOUNDS[1]) / 2,
             (REGION_BOUNDS[2] + REGION_BOUNDS[3]) / 2]  # Center of the region
MAP_ZOOM = 6