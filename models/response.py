"""
Response modellen voor de NPR Parking Calculator API
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class CalculationResponse:
    """Response model voor parking calculatie"""
    zone: str
    tarief_per_eenheid: float
    eenheid: str
    totale_duur_minuten: int
    totaalbedrag: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone": self.zone,
            "tarief_per_eenheid": self.tarief_per_eenheid,
            "eenheid": self.eenheid,
            "totale_duur_minuten": self.totale_duur_minuten,
            "totaalbedrag": self.totaalbedrag
        }

@dataclass
class ErrorResponse:
    """Response model voor error responses"""
    error: str
    message: str
    code: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error,
            "message": self.message,
            "code": self.code
        }

@dataclass
class BAGAddress:
    """Model voor BAG adres informatie"""
    postcode: str
    huisnummer: int
    straat: str
    plaats: str
    latitude: float
    longitude: float
    
@dataclass
class NPRZone:
    """Model voor NPR zone informatie"""
    area_manager_id: int
    fare_calculation_code: str
    zone_name: str
    
@dataclass
class TariefPart:
    """Model voor een tarief deel uit de NPR dataset"""
    area_manager_id: int
    fare_calculation_code: str
    start_date: str
    end_date: str
    start_duration: int
    end_duration: int
    amount: float
    step_size: int
    cumulative_amount: float
    
@dataclass
class CalculationInput:
    """Input model voor de berekening"""
    postcode: str
    huisnummer: int
    starttijd: datetime
    eindtijd: datetime
    
    def validate(self) -> List[str]:
        """Valideer de input parameters"""
        errors = []
        
        if not self.postcode or len(self.postcode) != 6:
            errors.append("Postcode moet 6 karakters zijn")
            
        if not self.huisnummer or self.huisnummer < 1:
            errors.append("Huisnummer moet groter zijn dan 0")
            
        if not self.starttijd:
            errors.append("Starttijd is verplicht")
            
        if not self.eindtijd:
            errors.append("Eindtijd is verplicht")
            
        if self.starttijd and self.eindtijd and self.starttijd >= self.eindtijd:
            errors.append("Starttijd moet voor eindtijd liggen")
            
        return errors

@dataclass 
class NPRTariefStructuur:
    """Model voor NPR tariefstructuur informatie"""
    zone_id: str
    zone_naam: str
    tarieven: List[Dict[str, Any]]
    geldig_van: str
    geldig_tot: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "zone_naam": self.zone_naam,
            "tarieven": self.tarieven,
            "geldig_van": self.geldig_van,
            "geldig_tot": self.geldig_tot
        }

@dataclass
class BerekenResponse:
    """Response model voor parkeerkosten berekening"""
    zone: str
    zone_id: str
    adres: str
    start_tijd: str
    eind_tijd: str
    duur_minuten: int
    totaal_kosten: float
    berekening_details: List[Dict[str, Any]]
    tarief_structuur: NPRTariefStructuur
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone": self.zone,
            "zone_id": self.zone_id,
            "adres": self.adres,
            "start_tijd": self.start_tijd,
            "eind_tijd": self.eind_tijd,
            "duur_minuten": self.duur_minuten,
            "totaal_kosten": self.totaal_kosten,
            "berekening_details": self.berekening_details,
            "tarief_structuur": self.tarief_structuur.to_dict()
        } 