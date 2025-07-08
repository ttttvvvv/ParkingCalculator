# NPR Parkeren API

Een modulaire Flask API voor het berekenen van parkeerkosten op basis van echte NPR (Nationale Parkeerregister) gegevens en BAG (Basisregistratie Adressen en Gebouwen) adresvalidatie.

## 🚀 Functionaliteiten

- ✅ **NPR Tariefberekening**: Complete implementatie van NPR tariefstructuren met step-based pricing
- ✅ **Modulaire architectuur**: Services, routes, models en utils gescheiden
- ✅ **Meerdere zones**: Amsterdam en Utrecht centrum zones ondersteund
- ✅ **Complexe tarieven**: Ondersteuning voor datum/tijd-afhankelijke tarieven
- ✅ **API documentatie**: Uitgebreide endpoint documentatie
- ⚠️ **BAG API integratie**: Vereist API key voor volledige functionaliteit

## 📋 Vereisten

- Python 3.8+
- Virtual environment (aanbevolen)
- BAG API key van het Kadaster (voor adresvalidatie)

## 🛠️ Installatie

1. **Clone het project**:
```bash
cd ParkingNPRV1
```

2. **Activeer virtual environment**:
```bash
source venv/bin/activate  # macOS/Linux
# of
venv\Scripts\activate     # Windows
```

3. **Installeer dependencies** (reeds geïnstalleerd):
```bash
pip install -r requirements.txt
```

4. **Configureer BAG API key**:
   - Open `config.py`
   - Vervang `'YOUR_BAG_API_KEY_HERE'` met jouw echte API key
   - Verkrijg een API key via: https://www.kadaster.nl/zakelijk/registraties/basisregistraties/bag

## 🏃‍♂️ Starten

```bash
python3 app.py
```

De API is beschikbaar op: http://127.0.0.1:5000

## 📖 API Endpoints

### `GET /`
API documentatie en overzicht van alle endpoints.

### `POST /bereken`
Bereken parkeerkosten voor een adres en tijdsperiode.

**Request body:**
```json
{
  "postcode": "1012JS",
  "huisnummer": 1,
  "huisletter": "A",          // optioneel
  "huisnummertoevoeging": "1", // optioneel
  "start_tijd": "2025-01-15T10:00:00",
  "eind_tijd": "2025-01-15T14:00:00"
}
```

**Response:**
```json
{
  "zone": "Amsterdam 1012",
  "zone_id": "amsterdam_centrum_1012",
  "adres": "Damrak 1, 1012JS Amsterdam",
  "start_tijd": "2025-01-15T10:00:00",
  "eind_tijd": "2025-01-15T14:00:00",
  "duur_minuten": 240,
  "totaal_kosten": 24.00,
  "berekening_details": [...],
  "tarief_structuur": {...}
}
```

### `GET /zones`
Haal alle beschikbare parkeerzone op.

### `GET /zones/{zone_id}/tarief`
Haal tariefstructuur op voor een specifieke zone.

### `GET /health`
Health check van de API en onderliggende services.

## 🗃️ Data & Configuratie

### NPR Dataset
- **Bestand**: `dataset.csv` (8.764 records)
- **Scope**: Landelijke NPR tariefgegevens
- **Features**: Step-based pricing, datum/tijd-afhankelijk, complexe tariefcodes

### Ondersteunde Gebieden
- **Amsterdam centrum**: Postcodes 1012, 1013, 1017, 1018
- **Utrecht centrum**: Postcodes 3511, 3512

### Uitbreidbaar Design
Nieuwe steden/zones toevoegen in `config.py`:
```python
ZONE_MAPPINGS = {
    'nieuwe_stad': {
        '1234': 'nieuwe_stad_centrum_1234'
    }
}
```

## 🔧 BAG API Configuratie

### API Key Verkrijgen
1. Ga naar https://www.kadaster.nl/zakelijk/registraties/basisregistraties/bag
2. Klik op "BAG API Individuele Bevragingen"
3. Vraag een API key aan

### Configuratie
In `config.py`:
```python
BAG_API_CONFIG = {
    'base_url': 'https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2',
    'api_key': 'JOUW_ECHTE_API_KEY_HIER',  # Vervang deze!
    'timeout': 30,
    'headers': {
        'Accept': 'application/hal+json',
        'Content-Type': 'application/json'
    }
}
```

## 🏗️ Architectuur

```
ParkingNPRV1/
├── app.py                 # Main Flask application
├── config.py              # Configuration & API settings
├── requirements.txt       # Python dependencies
├── dataset.csv           # NPR tariff data (8,764 records)
├── models/
│   ├── __init__.py
│   └── response.py       # Data models & response structures
├── routes/
│   ├── __init__.py
│   └── bereken.py        # API endpoints
├── services/
│   ├── __init__.py
│   ├── bag.py            # BAG API service (address lookup)
│   ├── npr_zone.py       # Zone determination service
│   └── npr_tarief.py     # NPR tariff calculation service
└── utils/
    ├── __init__.py
    └── date_utils.py     # Date/time utilities
```

## 🧪 Testing

### Zonder BAG API Key
```bash
curl -X GET http://127.0.0.1:5000/zones
curl -X GET http://127.0.0.1:5000/health
```

### Met BAG API Key
```bash
curl -X POST http://127.0.0.1:5000/bereken \
  -H "Content-Type: application/json" \
  -d '{
    "postcode": "1012JS",
    "huisnummer": 1,
    "start_tijd": "2025-01-15T10:00:00",
    "eind_tijd": "2025-01-15T14:00:00"
  }'
```

## ⚠️ Wat nog nodig is voor volledige functionaliteit

1. **BAG API Key**: Voor adresvalidatie en coördinaten
2. **Productie configuratie**: Environment variables voor API keys
3. **Error handling**: Uitgebreidere foutafhandeling voor edge cases
4. **Caching**: Redis/memcached voor BAG API responses
5. **Rate limiting**: API rate limiting implementatie
6. **Logging**: Structured logging naar bestanden
7. **Tests**: Unit en integration tests
8. **Docker**: Containerization voor deployment

## 🔍 Status Check

### ✅ Wat werkt nu al:
- NPR data loading (8.764 records)
- Tariefstructuur endpoints
- Zone mapping systeem
- Health checks
- Complete API documentatie
- Modulaire code architectuur

### ⚠️ Wat BAG API key vereist:
- Adres naar coördinaten conversie
- Postcode/huisnummer validatie
- Volledige `/bereken` endpoint functionaliteit

## 📞 Support

Voor vragen over:
- **NPR API**: Bekijk de code en documentatie
- **BAG API**: https://www.kadaster.nl/zakelijk/registraties/basisregistraties/bag
- **Issues**: Maak een GitHub issue aan

## 📄 Licentie

Dit project is gelicenseerd onder de MIT License. 