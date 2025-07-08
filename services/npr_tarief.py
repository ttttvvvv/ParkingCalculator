"""
NPR Tarief Service voor complexe tariefberekeningen
"""

import pandas as pd
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from models.response import NPRZone, TariefPart, CalculationResponse
from utils.date_utils import format_npr_date, is_date_in_range
from config import NPR_CONFIG, DEFAULT_CALCULATION_DATE

logger = logging.getLogger(__name__)

class NPRTariefService:
    """Service voor het berekenen van NPR parkeerkosten"""
    
    def __init__(self):
        self.tarief_data = None
        self.load_tarief_data()
    
    def load_tarief_data(self) -> bool:
        """Laad de NPR tariefdata uit CSV bestand"""
        try:
            self.tarief_data = pd.read_csv(NPR_CONFIG['csv_file'])
            logger.info(f"NPR tariefdata geladen: {len(self.tarief_data)} records")
            return True
        except Exception as e:
            logger.error(f"Fout bij laden NPR tariefdata: {e}")
            return False
    
    def bereken_kosten(self, zone_info: Dict[str, Any], start_tijd: datetime, eind_tijd: datetime) -> Optional[Dict[str, Any]]:
        """
        Bereken parkeerkosten voor een zone en tijdsperiode
        
        Args:
            zone_info: Dictionary met zone informatie (area_manager_id, fare_calculation_code, etc.)
            start_tijd: Start datetime
            eind_tijd: Eind datetime
            
        Returns:
            Dictionary met kosten berekening
        """
        try:
            area_manager_id = zone_info['area_manager_id']
            fare_calculation_code = zone_info['fare_calculation_code']
            
            # Bereken duur in minuten
            duration = eind_tijd - start_tijd
            duration_minutes = int(duration.total_seconds() / 60)
            
            if duration_minutes <= 0:
                return None
            
            # Format calculation date
            calc_date = start_tijd.strftime("%Y%m%d")
            
            # Haal tariefparts op
            tarief_parts = self._get_tarief_parts(area_manager_id, fare_calculation_code, calc_date)
            
            if not tarief_parts:
                logger.warning(f"Geen tariefparts gevonden voor Area {area_manager_id}, Code {fare_calculation_code}")
                return None
            
            # Bereken totale kosten
            total_cost, tarief_info = self._calculate_total_cost(tarief_parts, duration_minutes)
            
            # Bouw details
            details = []
            for part in tarief_parts[:3]:  # Top 3 parts voor details
                details.append({
                    'start_duration': part.start_duration,
                    'end_duration': part.end_duration,
                    'amount_per_step': part.amount,
                    'step_size_minutes': part.step_size
                })
            
            return {
                'duur_minuten': duration_minutes,
                'totaal_kosten': round(total_cost, 2),
                'details': details,
                'tarief_info': tarief_info
            }
            
        except Exception as e:
            logger.error(f"Fout bij berekenen kosten: {e}")
            return None
    
    def _get_tarief_parts(self, area_manager_id: int, fare_calculation_code: str, 
                         calc_date: str) -> List[TariefPart]:
        """
        Haal tariefstructuur op voor een specifieke zone en datum
        
        Args:
            area_manager_id: NPR Area Manager ID
            fare_calculation_code: NPR Fare Calculation Code
            calc_date: Datum voor berekening (YYYYMMDD)
            
        Returns:
            List van TariefPart objecten
        """
        try:
            # Filter data voor deze zone en code
            zone_data = self.tarief_data[
                (self.tarief_data['AreaManagerId'] == area_manager_id) &
                (self.tarief_data['FareCalculationCode'] == fare_calculation_code)
            ]
            
            if zone_data.empty:
                logger.warning(f"Geen data gevonden voor Area {area_manager_id}, Code {fare_calculation_code}")
                return []
            
            # Filter voor geldige datum
            valid_tariffs = []
            for _, row in zone_data.iterrows():
                start_date = str(row['StartDateFarePart'])
                end_date = str(row['EndDateFarePart'])
                
                if is_date_in_range(calc_date, start_date, end_date):
                    valid_tariffs.append(TariefPart(
                        area_manager_id=row['AreaManagerId'],
                        fare_calculation_code=row['FareCalculationCode'],
                        start_date=start_date,
                        end_date=end_date,
                        start_duration=row['StartDurationFarePart'],
                        end_duration=row['EndDurationFarePart'],
                        amount=row['AmountFarePart'],
                        step_size=row['StepSizeFarePart'],
                        cumulative_amount=row['AmountCumulative']
                    ))
            
            # Sorteer op start duration
            valid_tariffs.sort(key=lambda x: x.start_duration)
            
            logger.info(f"Gevonden {len(valid_tariffs)} geldige tariefparts voor {calc_date}")
            return valid_tariffs
            
        except Exception as e:
            logger.error(f"Fout bij ophalen tariefparts: {e}")
            return []
    
    def _calculate_total_cost(self, tarief_parts: List[TariefPart], 
                            duration_minutes: int) -> Tuple[float, Dict[str, Any]]:
        """
        Bereken totale kosten op basis van tariefstructuur
        
        Args:
            tarief_parts: List van TariefPart objecten
            duration_minutes: Parkeerduur in minuten
            
        Returns:
            Tuple van (totale_kosten, tarief_info)
        """
        try:
            total_cost = 0.0
            remaining_duration = duration_minutes
            tarief_info = {
                "tarief_per_eenheid": 0.0,
                "eenheid": "minuten"
            }
            
            for part in tarief_parts:
                if remaining_duration <= 0:
                    break
                    
                # Bepaal hoeveel minuten van deze part gebruikt worden
                part_start = part.start_duration
                part_end = part.end_duration
                
                # Als we nog niet bij deze part zijn, ga door
                if duration_minutes - remaining_duration < part_start:
                    continue
                    
                # Bereken hoeveel minuten in deze part vallen
                minutes_in_part = min(
                    remaining_duration,
                    part_end - max(part_start, duration_minutes - remaining_duration)
                )
                
                if minutes_in_part > 0:
                    # Bereken kosten voor dit deel
                    part_cost = self._calculate_part_cost(part, minutes_in_part)
                    total_cost += part_cost
                    
                    # Update tarief info met het eerste relevante tarief
                    if tarief_info["tarief_per_eenheid"] == 0.0:
                        tarief_info["tarief_per_eenheid"] = part.amount
                        tarief_info["eenheid"] = f"{part.step_size} minuten"
                    
                    remaining_duration -= minutes_in_part
                    
                    logger.debug(f"Part {part_start}-{part_end}: {minutes_in_part} min, €{part_cost:.2f}")
            
            # Als er nog resterende duur is, gebruik het laatste tarief
            if remaining_duration > 0 and tarief_parts:
                last_part = tarief_parts[-1]
                if last_part.end_duration == 999999:  # Oneindige duur
                    part_cost = self._calculate_part_cost(last_part, remaining_duration)
                    total_cost += part_cost
                    
                    logger.debug(f"Resterende duur: {remaining_duration} min, €{part_cost:.2f}")
            
            return total_cost, tarief_info
            
        except Exception as e:
            logger.error(f"Fout bij berekenen totale kosten: {e}")
            return 0.0, {"tarief_per_eenheid": 0.0, "eenheid": "minuten"}
    
    def _calculate_part_cost(self, part: TariefPart, minutes: int) -> float:
        """
        Bereken kosten voor een specifiek tariefpart
        
        Args:
            part: TariefPart object
            minutes: Aantal minuten
            
        Returns:
            Kosten voor dit deel
        """
        try:
            if minutes <= 0:
                return 0.0
                
            # Bereken aantal stappen (rounded up)
            steps = (minutes + part.step_size - 1) // part.step_size
            
            # Totale kosten = aantal stappen * bedrag per stap
            cost = steps * part.amount
            
            # Voeg cumulatieve kosten toe
            cost += part.cumulative_amount
            
            return cost
            
        except Exception as e:
            logger.error(f"Fout bij berekenen part kosten: {e}")
            return 0.0
    
    def get_tarief_structuur(self, zone_info: Dict[str, Any]) -> Optional[Any]:
        """
        Haal tariefstructuur op voor een zone
        
        Args:
            zone_info: Dictionary met zone informatie
            
        Returns:
            NPRTariefStructuur object
        """
        try:
            from models.response import NPRTariefStructuur
            
            area_manager_id = zone_info['area_manager_id']
            fare_calculation_code = zone_info['fare_calculation_code']
            
            # Gebruik huidige datum voor berekening
            calc_date = datetime.now().strftime("%Y%m%d")
            
            # Haal tariefparts op
            tarief_parts = self._get_tarief_parts(area_manager_id, fare_calculation_code, calc_date)
            
            if not tarief_parts:
                return None
            
            # Converteer naar tarieven lijst
            tarieven = []
            for part in tarief_parts:
                tarieven.append({
                    'start_duration': part.start_duration,
                    'end_duration': part.end_duration,
                    'amount': part.amount,
                    'step_size': part.step_size,
                    'cumulative_amount': part.cumulative_amount
                })
            
            return NPRTariefStructuur(
                zone_id=zone_info.get('zone_id', f"{area_manager_id}_{fare_calculation_code}"),
                zone_naam=zone_info.get('zone_naam', f"Zone {area_manager_id}"),
                tarieven=tarieven,
                geldig_van=calc_date,
                geldig_tot="99991231"  # Default ver in de toekomst
            )
            
        except Exception as e:
            logger.error(f"Fout bij ophalen tariefstructuur: {e}")
            return None
    
    def validate_zone_tariff(self, zone: NPRZone, calc_date: str = None) -> bool:
        """
        Valideer of er een geldig tarief bestaat voor een zone
        
        Args:
            zone: NPRZone object
            calc_date: Datum voor berekening (YYYYMMDD)
            
        Returns:
            True als geldig tarief bestaat, False anders
        """
        try:
            calc_date = calc_date or DEFAULT_CALCULATION_DATE
            
            tarief_parts = self._get_tarief_parts(
                zone.area_manager_id,
                zone.fare_calculation_code,
                calc_date
            )
            
            return len(tarief_parts) > 0
            
        except Exception as e:
            logger.error(f"Fout bij valideren zone tarief: {e}")
            return False
    
    def health_check(self) -> bool:
        """Controleer of de tariefservice werkt"""
        try:
            return self.tarief_data is not None and len(self.tarief_data) > 0
        except:
            return False 