"""
Datum en tijd utilities voor NPR Parking Calculator
"""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def parse_iso_datetime(datetime_str: str) -> Optional[datetime]:
    """Parse een ISO datetime string naar een datetime object"""
    try:
        # Ondersteun verschillende formaten
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
                
        logger.error(f"Kan datetime string niet parsen: {datetime_str}")
        return None
        
    except Exception as e:
        logger.error(f"Fout bij parsen van datetime: {e}")
        return None

def format_npr_date(date_obj: datetime) -> str:
    """Format een datetime object naar NPR datum format (YYYYMMDD)"""
    return date_obj.strftime("%Y%m%d")

def calculate_duration_minutes(start_time: datetime, end_time: datetime) -> int:
    """Bereken de duur tussen twee tijdstippen in minuten"""
    if start_time >= end_time:
        return 0
    
    duration = end_time - start_time
    return int(duration.total_seconds() / 60)

def is_date_in_range(check_date: str, start_date: str, end_date: str) -> bool:
    """Controleer of een datum binnen een bepaald bereik valt"""
    try:
        # NPR dates zijn in YYYYMMDD format
        check_int = int(check_date)
        start_int = int(start_date)
        end_int = int(end_date)
        
        return start_int <= check_int <= end_int
    except ValueError:
        logger.error(f"Ongeldige datum formaten: {check_date}, {start_date}, {end_date}")
        return False

def get_weekday_from_date(date_str: str) -> int:
    """Krijg weekdag van een datum string (0=Maandag, 6=Zondag)"""
    try:
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.weekday()
    except ValueError:
        logger.error(f"Ongeldige datum format: {date_str}")
        return 0

def format_duration_display(minutes: int) -> str:
    """Format een duur in minuten naar een leesbare string"""
    if minutes < 60:
        return f"{minutes} minuten"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours} uur"
    else:
        return f"{hours} uur en {remaining_minutes} minuten"

def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """Parse een datetime string naar een datetime object (alias voor parse_iso_datetime)"""
    return parse_iso_datetime(datetime_str)

def validate_time_range(start_time: datetime, end_time: datetime) -> bool:
    """Valideer of een tijdsbereik geldig is (start_time < end_time)"""
    try:
        return start_time < end_time
    except Exception as e:
        logger.error(f"Fout bij valideren tijdsbereik: {e}")
        return False 