"""
Routes voor parkeerkosten berekening
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from typing import Dict, Any

from services.npr_zone import NPRZoneService
from services.npr_tarief import NPRTariefService
from models.response import BerekenResponse, NPRTariefStructuur
from utils.date_utils import parse_datetime, validate_time_range

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bereken_bp = Blueprint('bereken', __name__)

# Initialize services
zone_service = NPRZoneService()
tarief_service = NPRTariefService()

@bereken_bp.route('/bereken', methods=['POST'])
def bereken_parkeerkosten():
    """Bereken parkeerkosten op basis van adres en tijdsperiode"""
    try:
        # Valideer input
        data = request.get_json()
        if not data:
            return jsonify({"error": "Geen JSON data ontvangen"}), 400
        
        # Verplichte velden
        required_fields = ['postcode', 'huisnummer', 'start_tijd', 'eind_tijd']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Veld '{field}' is verplicht"}), 400
        
        postcode = data['postcode']
        huisnummer = str(data['huisnummer'])
        huisletter = data.get('huisletter')
        huisnummertoevoeging = data.get('huisnummertoevoeging')
        start_tijd = data['start_tijd']
        eind_tijd = data['eind_tijd']
        
        logger.info(f"Bereken parkeerkosten voor {postcode} {huisnummer} van {start_tijd} tot {eind_tijd}")
        
        # Parse datums
        start_dt = parse_datetime(start_tijd)
        eind_dt = parse_datetime(eind_tijd)
        
        if not start_dt or not eind_dt:
            return jsonify({"error": "Ongeldige datum/tijd formaat. Gebruik ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
        
        # Valideer tijdsperiode
        if not validate_time_range(start_dt, eind_dt):
            return jsonify({"error": "Eind tijd moet na start tijd liggen"}), 400
        
        # Bepaal zone via automatische discovery
        zone_info = zone_service.get_zone_by_address(
            postcode, huisnummer, huisletter, huisnummertoevoeging
        )
        
        if not zone_info:
            return jsonify({
                "error": "Geen parkeerzone gevonden voor dit adres",
                "details": f"Adres {postcode} {huisnummer} kon niet gekoppeld worden aan een NPR zone",
                "suggestion": "Probeer een ander adres of controleer de postcode"
            }), 404
        
        # Bepaal tariefstructuur voor deze zone
        tarief_structuur = tarief_service.get_tarief_structuur(zone_info)
        
        if not tarief_structuur:
            return jsonify({
                "error": "Geen tariefgegevens gevonden voor deze zone",
                "zone": zone_info['zone_naam'],
                "zone_details": {
                    "area_manager_id": zone_info['area_manager_id'],
                    "fare_calculation_code": zone_info['fare_calculation_code']
                }
            }), 404
        
        # Bereken kosten
        kosten_berekening = tarief_service.bereken_kosten(zone_info, start_dt, eind_dt)
        
        if not kosten_berekening:
            return jsonify({
                "error": "Kan parkeerkosten niet berekenen",
                "zone": zone_info['zone_naam']
            }), 500
        
        # Bouw response
        response = BerekenResponse(
            zone=zone_info['zone_naam'],
            zone_id=zone_info['zone_id'],
            adres=f"{zone_info['adres']['straatnaam']} {huisnummer}, {postcode} {zone_info['adres']['woonplaats']}",
            start_tijd=start_tijd,
            eind_tijd=eind_tijd,
            duur_minuten=kosten_berekening['duur_minuten'],
            totaal_kosten=kosten_berekening['totaal_kosten'],
            berekening_details=kosten_berekening['details'],
            tarief_structuur=tarief_structuur
        )
        
        # Voeg extra metadata toe
        response_dict = response.to_dict()
        response_dict['zone_detection'] = {
            'method': zone_info.get('detection_method', 'automatic'),
            'area_manager_id': zone_info['area_manager_id'],
            'fare_calculation_code': zone_info['fare_calculation_code'],
            'coordinates': zone_info.get('coordinates')
        }
        
        return jsonify(response_dict), 200
        
    except Exception as e:
        logger.error(f"Fout bij berekenen parkeerkosten: {e}")
        return jsonify({"error": "Interne server fout", "details": str(e)}), 500

@bereken_bp.route('/zones', methods=['GET'])
def get_zones():
    """Haal alle beschikbare parkeerzone op"""
    try:
        zones = zone_service.get_available_zones()
        return jsonify(zones), 200
    except Exception as e:
        logger.error(f"Fout bij ophalen zones: {e}")
        return jsonify({"error": "Kan zones niet ophalen"}), 500

@bereken_bp.route('/zones/search', methods=['GET'])
def search_zones():
    """Zoek zones op naam of code"""
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({"error": "Query parameter 'q' is verplicht"}), 400
        
        results = zone_service.search_zones_by_name(search_term)
        return jsonify({
            "query": search_term,
            "results": results,
            "count": len(results)
        }), 200
    except Exception as e:
        logger.error(f"Fout bij zoeken zones: {e}")
        return jsonify({"error": "Kan zones niet zoeken"}), 500

@bereken_bp.route('/zones/<zone_id>/tarief', methods=['GET'])
def get_zone_tarief(zone_id: str):
    """Haal tariefstructuur op voor een specifieke zone"""
    try:
        # Haal zone info op
        zone_info = zone_service.get_zone_by_id(zone_id)
        if not zone_info:
            return jsonify({"error": f"Zone {zone_id} niet gevonden"}), 404
        
        # Haal tariefstructuur op
        tarief_structuur = tarief_service.get_tarief_structuur(zone_info)
        
        if not tarief_structuur:
            return jsonify({"error": f"Geen tariefgegevens gevonden voor zone {zone_id}"}), 404
        
        return jsonify(tarief_structuur.to_dict()), 200
    except Exception as e:
        logger.error(f"Fout bij ophalen tarief voor zone {zone_id}: {e}")
        return jsonify({"error": "Kan tariefgegevens niet ophalen"}), 500

@bereken_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        zone_check = zone_service.health_check()
        tarief_check = tarief_service.health_check()
        
        zone_count = len(zone_service.available_zones)
        
        status = "healthy" if zone_check and tarief_check else "unhealthy"
        
        return jsonify({
            "status": status,
            "services": {
                "zone_service": "ok" if zone_check else "error",
                "tarief_service": "ok" if tarief_check else "error"
            },
            "data": {
                "zones_loaded": zone_count,
                "auto_discovery": True
            },
            "timestamp": datetime.now().isoformat()
        }), 200 if status == "healthy" else 503
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503 