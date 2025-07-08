"""
NPR Zone Service voor het bepalen van parkeerzone
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any, List
from services.bag import BAGService
from config import NPR_CONFIG

logger = logging.getLogger(__name__)

class NPRZoneService:
    """Service voor automatische NPR zone discovery en bepaling"""
    
    def __init__(self):
        self.bag_service = BAGService()
        self.available_zones = {}
        self.postcode_to_zone_cache = {}
        self._load_all_npr_zones()
    
    def _load_all_npr_zones(self):
        """Laad alle beschikbare NPR zones uit de dataset"""
        try:
            logger.info("Loading alle NPR zones uit dataset...")
            df = pd.read_csv(NPR_CONFIG['csv_file'])
            
            # Groepeer op AreaManagerId en FareCalculationCode
            zone_groups = df.groupby(['AreaManagerId', 'FareCalculationCode']).size().reset_index(name='count')
            
            self.available_zones = {}
            for _, row in zone_groups.iterrows():
                area_id = int(row['AreaManagerId'])
                fare_code = str(row['FareCalculationCode'])
                
                # Skip NaN fare codes
                if fare_code == 'nan':
                    continue
                    
                zone_key = f"{area_id}_{fare_code}"
                
                self.available_zones[zone_key] = {
                    'area_manager_id': area_id,
                    'fare_calculation_code': fare_code,
                    'zone_id': zone_key,
                    'zone_naam': f"Zone {area_id} - {fare_code}",
                    'record_count': int(row['count'])
                }
            
            logger.info(f"Geladen {len(self.available_zones)} NPR zones")
            
            # Log enkele voorbeelden
            for i, (zone_key, zone_info) in enumerate(list(self.available_zones.items())[:5]):
                logger.info(f"Zone {i+1}: {zone_key} ({zone_info['record_count']} records)")
                
        except Exception as e:
            logger.error(f"Fout bij laden NPR zones: {e}")
            self.available_zones = {}
    
    def get_zone_by_address(self, postcode: str, huisnummer: str, 
                          huisletter: Optional[str] = None,
                          huisnummertoevoeging: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Bepaal de beste NPR zone voor een adres met automatische zone discovery
        """
        try:
            postcode_clean = postcode.replace(" ", "").upper()
            postcode_cijfers = postcode_clean[:4]
            
            # Probeer eerst adresgegevens op te halen via BAG API
            adres_data = None
            try:
                adres_data = self.bag_service.get_adres_by_postcode_huisnummer(
                    postcode, huisnummer, huisletter, huisnummertoevoeging
                )
            except Exception as e:
                logger.warning(f"BAG API fout voor {postcode} {huisnummer}: {e}")
            
            # Gebruik dummy adresgegevens als BAG API faalt
            if not adres_data:
                logger.info(f"Geen BAG data, gebruik postcode {postcode_clean} voor zone discovery")
                adres_data = {
                    'straatnaam': 'Onbekend',
                    'woonplaats': self._guess_city_from_postcode(postcode_cijfers),
                    'gemeente': self._guess_city_from_postcode(postcode_cijfers).lower(),
                    'coordinates': None
                }
            
            # Probeer zone te vinden via verschillende strategieën
            zone_info = self._find_best_zone_for_postcode(postcode_clean, adres_data)
            
            # ALTIJD een zone teruggeven - gebruik fallback als nodig
            if not zone_info:
                logger.warning(f"Geen specifieke zone gevonden, gebruik fallback voor {postcode}")
                zone_info = self._get_fallback_zone()
            
            if zone_info:
                return {
                    'zone_id': zone_info['zone_id'],
                    'zone_naam': zone_info['zone_naam'],
                    'area_manager_id': zone_info['area_manager_id'],
                    'fare_calculation_code': zone_info['fare_calculation_code'],
                    'adres': adres_data,
                    'coordinates': adres_data.get('coordinates'),
                    'detection_method': zone_info.get('detection_method', 'automatic')
                }
            
            logger.error(f"Kan geen enkele zone vinden voor {postcode}")
            return None
            
        except Exception as e:
            logger.error(f"Fout bij bepalen zone voor {postcode} {huisnummer}: {e}")
            # Ook bij fout een fallback zone geven
            zone_info = self._get_fallback_zone()
            if zone_info:
                return {
                    'zone_id': zone_info['zone_id'],
                    'zone_naam': zone_info['zone_naam'],
                    'area_manager_id': zone_info['area_manager_id'],
                    'fare_calculation_code': zone_info['fare_calculation_code'],
                    'adres': {'straatnaam': 'Onbekend', 'woonplaats': 'Onbekend', 'gemeente': 'onbekend'},
                    'coordinates': None,
                    'detection_method': 'error_fallback'
                }
            return None
    
    def _guess_city_from_postcode(self, postcode_cijfers: str) -> str:
        """Raad stad op basis van postcode (eerste 4 cijfers)"""
        pc_int = int(postcode_cijfers)
        
        if 1000 <= pc_int <= 1299:
            return 'Amsterdam'
        elif 3000 <= pc_int <= 3299:
            return 'Rotterdam'
        elif 3500 <= pc_int <= 3599:
            return 'Utrecht'
        elif 2500 <= pc_int <= 2699:
            return 'Den Haag'
        else:
            return 'Nederland'
    
    def _get_fallback_zone(self) -> Optional[Dict[str, Any]]:
        """Haal een betrouwbare fallback zone op"""
        if not self.available_zones:
            return None
        
        # Zoek naar meest populaire zones
        sorted_zones = sorted(
            self.available_zones.items(),
            key=lambda x: x[1]['record_count'],
            reverse=True
        )
        
        if sorted_zones:
            zone_key, zone_info = sorted_zones[0]
            zone_info_copy = zone_info.copy()
            zone_info_copy['detection_method'] = 'fallback_most_popular'
            logger.info(f"Gebruik fallback zone: {zone_key} ({zone_info['record_count']} records)")
            return zone_info_copy
        
        return None
    
    def _find_best_zone_for_postcode(self, postcode: str, adres_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Vind de beste zone voor een postcode met verschillende strategieën"""
        
        postcode_clean = postcode.replace(" ", "").upper()
        postcode_cijfers = postcode_clean[:4]
        gemeente = adres_data.get('gemeente', '').lower()
        
        # Cache check
        cache_key = f"{postcode_clean}_{gemeente}"
        if cache_key in self.postcode_to_zone_cache:
            return self.postcode_to_zone_cache[cache_key]
        
        # Strategie 1: Bekende steden met populaire zones
        best_zone = self._find_zone_by_city_heuristics(gemeente, postcode_cijfers)
        if best_zone:
            best_zone['detection_method'] = 'city_heuristics'
            self.postcode_to_zone_cache[cache_key] = best_zone
            return best_zone
        
        # Strategie 2: Meest populaire zone (meeste records)
        best_zone = self._find_most_popular_zone()
        if best_zone:
            best_zone['detection_method'] = 'most_popular'
            self.postcode_to_zone_cache[cache_key] = best_zone
            return best_zone
        
        return None
    
    def _find_zone_by_city_heuristics(self, gemeente: str, postcode_cijfers: str) -> Optional[Dict[str, Any]]:
        """Gebruik stad-specifieke heuristieken om zones te vinden"""
        
        city_patterns = {
            'amsterdam': [
                (14, ['TAR01', 'TAR02', 'TAR03', 'TAR04']),
                (14, ['14_DAGTAR', 'PRTAR01'])
            ],
            'utrecht': [
                (34, ['34_TAR01', '34_TAR02']),
                (34, ['34_DAG01', '34_DAG02'])
            ],
            'rotterdam': [
                (17, ['TAR01', 'GAR01']),  # Gebruik echte beschikbare zones
                (5, ['PR01'])
            ],
            'den haag': [
                (10, ['TAR01', 'CPL01']),
                (3, ['PR01'])
            ]
        }
        
        if gemeente in city_patterns:
            for area_id, fare_codes in city_patterns[gemeente]:
                for fare_code in fare_codes:
                    zone_key = f"{area_id}_{fare_code}"
                    if zone_key in self.available_zones:
                        logger.info(f"Gevonden zone via stad heuristiek: {zone_key} voor {gemeente}")
                        zone_info = self.available_zones[zone_key].copy()
                        zone_info['detection_method'] = 'city_heuristics'
                        return zone_info
        
        return None
    
    def _find_most_popular_zone(self) -> Optional[Dict[str, Any]]:
        """Vind de zone met de meeste records als fallback"""
        return self._get_fallback_zone()
    
    def get_available_zones(self) -> Dict[str, Any]:
        """Haal alle beschikbare zones op"""
        zones = []
        
        for zone_key, zone_info in self.available_zones.items():
            zones.append({
                'zone_id': zone_info['zone_id'],
                'zone_naam': zone_info['zone_naam'],
                'area_manager_id': zone_info['area_manager_id'],
                'fare_calculation_code': zone_info['fare_calculation_code'],
                'record_count': zone_info['record_count']
            })
        
        # Sorteer op populariteit
        zones.sort(key=lambda x: x['record_count'], reverse=True)
        
        return {
            'zones': zones,
            'total': len(zones)
        }
    
    def search_zones_by_name(self, search_term: str) -> List[Dict[str, Any]]:
        """Zoek zones op naam of code"""
        results = []
        search_term = search_term.lower()
        
        for zone_key, zone_info in self.available_zones.items():
            if (search_term in zone_info['zone_naam'].lower() or 
                search_term in zone_info['fare_calculation_code'].lower() or
                search_term in str(zone_info['area_manager_id'])):
                results.append(zone_info.copy())
        
        return results
    
    def get_zone_by_id(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """Haal een specifieke zone op via zone_id"""
        return self.available_zones.get(zone_id)
    
    def health_check(self) -> bool:
        """Controleer of de zone service werkt"""
        try:
            bag_healthy = self.bag_service.health_check()
            zones_loaded = len(self.available_zones) > 0
            return bag_healthy and zones_loaded
        except:
            return False 