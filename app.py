"""
NPR Parking Calculator - Flask Application
"""

from flask import Flask, jsonify
import logging
import os
from config import SERVER_CONFIG
from routes.bereken import bereken_bp
from services.npr_tarief import NPRTariefService
from services.npr_zone import NPRZoneService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Initialize services (dit triggert automatische zone loading)
logger.info("Initialiseer NPR services...")
zone_service = NPRZoneService()
tarief_service = NPRTariefService()

# Register blueprints
app.register_blueprint(bereken_bp)

@app.route('/')
def index():
    """API documentatie endpoint"""
    zone_count = len(zone_service.available_zones)
    
    return jsonify({
        "name": "NPR Parkeren API",
        "version": "2.0.0",
        "description": "API voor het berekenen van parkeerkosten met automatische NPR zone discovery",
        "features": [
            "Automatische zone discovery",
            "BAG API integratie", 
            "NPR tariefberekeningen",
            "Support voor alle Nederlandse postcodes"
        ],
        "zones_loaded": zone_count,
        "endpoints": {
            "POST /bereken": "Bereken parkeerkosten voor een adres",
            "GET /zones": "Lijst alle beschikbare zones",
            "GET /zones/search?q=<term>": "Zoek zones op naam/code",
            "GET /zones/<zone_id>/tarief": "Haal tariefstructuur op",
            "GET /health": "Health check"
        },
        "example_request": {
            "url": "/bereken",
            "method": "POST",
            "body": {
                "postcode": "1012 AB",
                "huisnummer": "1",
                "start_tijd": "2024-01-15T09:00:00",
                "eind_tijd": "2024-01-15T17:00:00"
            }
        }
    })

if __name__ == '__main__':
    logger.info(f"Starting NPR Parkeren API op {SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}")
    logger.info(f"Debug mode: {SERVER_CONFIG['debug']}")
    logger.info(f"Geladen zones: {len(zone_service.available_zones)}")
    
    app.run(
        host=SERVER_CONFIG['host'],
        port=SERVER_CONFIG['port'],
        debug=SERVER_CONFIG['debug']
    ) 