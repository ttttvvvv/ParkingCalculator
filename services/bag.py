"""
BAG API Service voor het ophalen van adresgegevens
"""

import requests
import logging
from typing import Optional, Dict, Any
from config import BAG_CONFIG

logger = logging.getLogger(__name__)

class BAGService:
    """Service voor het ophalen van adresgegevens via de BAG API"""
    
    def __init__(self):
        self.base_url = BAG_CONFIG['base_url']
        self.api_key = BAG_CONFIG['api_key']
        self.timeout = BAG_CONFIG['timeout']
        self.headers = BAG_CONFIG['headers'].copy()
        
        # Voeg API key toe aan headers indien beschikbaar
        if self.api_key:
            self.headers['X-Api-Key'] = self.api_key
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Maak een request naar de BAG API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.info(f"BAG API request: {url} met params: {params}")
            
            response = requests.get(
                url, 
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            logger.info(f"BAG API response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("BAG API authenticatie gefaald - controleer je API key")
                return None
            elif response.status_code == 404:
                logger.warning(f"Geen resultaten gevonden voor {url}")
                return None
            else:
                logger.error(f"BAG API error: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            logger.error(f"BAG API timeout na {self.timeout}s voor {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"BAG API request error: {e}")
            return None
    
    def get_adres_by_postcode_huisnummer(self, postcode: str, huisnummer: str, 
                                        huisletter: Optional[str] = None, 
                                        huisnummertoevoeging: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Zoek adresgegevens op basis van postcode en huisnummer via de BAG API
        
        Args:
            postcode: Postcode (bijv. "1012JS")
            huisnummer: Huisnummer 
            huisletter: Optionele huisletter
            huisnummertoevoeging: Optionele huisnummertoevoeging
            
        Returns:
            Dict met adresgegevens en coördinaten of None als niet gevonden
        """
        # Normaliseer postcode (verwijder spaties)
        postcode = postcode.replace(" ", "").upper()
        
        # Bouw parameters
        params = {
            'postcode': postcode,
            'huisnummer': huisnummer
        }
        
        if huisletter:
            params['huisletter'] = huisletter
        if huisnummertoevoeging:
            params['huisnummertoevoeging'] = huisnummertoevoeging
            
        # Zoek adressen via de adressen endpoint
        result = self._make_request('adressen', params)
        
        if not result or not result.get('_embedded', {}).get('adressen'):
            logger.warning(f"Geen adres gevonden voor {postcode} {huisnummer}")
            return None
        
        # Neem het eerste adres uit de resultaten
        adres = result['_embedded']['adressen'][0]
        
        # Haal coördinaten op van het verblijfsobject
        verblijfsobject_url = adres.get('_links', {}).get('adresseertVerblijfsobject', {}).get('href')
        
        if verblijfsobject_url:
            # Extract verblijfsobject ID from URL
            verblijfsobject_id = verblijfsobject_url.split('/')[-1]
            verblijfsobject = self._make_request(f'verblijfsobjecten/{verblijfsobject_id}')
            
            if verblijfsobject and verblijfsobject.get('geometrie'):
                coordinates = verblijfsobject['geometrie']['coordinates']
                return {
                    'postcode': adres.get('postcode'),
                    'huisnummer': adres.get('huisnummer'),
                    'huisletter': adres.get('huisletter'),
                    'huisnummertoevoeging': adres.get('huisnummertoevoeging'),
                    'straatnaam': adres.get('openbareRuimteNaam'),
                    'woonplaats': adres.get('woonplaatsNaam'),
                    'gemeente': adres.get('gemeenteNaam'),
                    'coordinates': {
                        'lat': coordinates[1],  # BAG gebruikt [lng, lat] format
                        'lng': coordinates[0]
                    }
                }
        
        # Fallback zonder coördinaten
        return {
            'postcode': adres.get('postcode'),
            'huisnummer': adres.get('huisnummer'),
            'huisletter': adres.get('huisletter'),
            'huisnummertoevoeging': adres.get('huisnummertoevoeging'),
            'straatnaam': adres.get('openbareRuimteNaam'),
            'woonplaats': adres.get('woonplaatsNaam'),
            'gemeente': adres.get('gemeenteNaam'),
            'coordinates': None
        }
    
    def health_check(self) -> bool:
        """Controleer of de BAG API beschikbaar is"""
        try:
            # Probeer een simpele request naar de root endpoint
            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=5
            )
            return response.status_code in [200, 404]  # 404 is ook OK voor root endpoint
        except:
            return False 