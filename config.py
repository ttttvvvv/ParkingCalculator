"""
Configuratie voor de NPR Parking Calculator
"""

import os
from datetime import datetime

# Flask configuratie
DEBUG = True
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

# BAG API configuratie
BAG_CONFIG = {
    'base_url': 'https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2',
    'api_key': 'BAG_API_KEY',  # Moet worden ingesteld via environment variable
    'timeout': 30,
    'headers': {
        'Accept': 'application/hal+json',
        'Content-Type': 'application/hal+json'
    }
}

# NPR Dataset configuratie voor automatische zone discovery
NPR_CONFIG = {
    'csv_file': 'data/dataset.csv',
    'encoding': 'utf-8',
    'datetime_format': '%Y-%m-%d %H:%M:%S'
}

# Development server configuratie
SERVER_CONFIG = {
    'host': '127.0.0.1',
    'port': 5001,  # Gewijzigd van 5000 naar 5001 om conflict te vermijden
    'debug': True
}

# NPR Data configuratie
NPR_DATASET_FILE = "dataset.csv"
NPR_ZONE_DATA_FILE = "zone_data.json"  # Voor als je zone geometrie data hebt

# Default zone mapping voor demo (kan later vervangen door echte geometrie)
DEFAULT_ZONE_MAPPING = {
    "1012": {"area_manager_id": 14, "fare_calculation_code": "TAR01", "zone_name": "Amsterdam Centrum"},
    "1013": {"area_manager_id": 14, "fare_calculation_code": "TAR02", "zone_name": "Amsterdam West"},
    "1017": {"area_manager_id": 14, "fare_calculation_code": "TAR03", "zone_name": "Amsterdam Zuid"},
    "1018": {"area_manager_id": 17, "fare_calculation_code": "TAR01", "zone_name": "Amsterdam Noord"},
    "3511": {"area_manager_id": 34, "fare_calculation_code": "34_TAR01", "zone_name": "Utrecht Centrum"},
    "3512": {"area_manager_id": 34, "fare_calculation_code": "34_TAR02", "zone_name": "Utrecht Oost"},
}

# Logging configuratie
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Cache configuratie
CACHE_TIMEOUT = 300  # 5 minuten cache voor BAG API calls

# Tijdzone
TIMEZONE = "Europe/Amsterdam"

# Standaard tariefperiode voor berekeningen
DEFAULT_CALCULATION_DATE = datetime.now().strftime("%Y%m%d") 