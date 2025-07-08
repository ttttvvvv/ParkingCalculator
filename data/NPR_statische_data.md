
# Nationaal Parkeer Register (NPR) – Datasetbeschrijving

Deze `.md`-file beschrijft de **statische datasets** van het Nationaal Parkeer Register (NPR) zoals verstrekt via de RDW (opendata.rdw.nl).

## 📌 Bronnen

- RDW Open Data: https://opendata.rdw.nl
- Beschrijving statische data (PDF): `Beschrijving dataset statische parkeergegevens (1).pdf`
- Nationaal Parkeer Register: https://www.nationaalparkeerregister.nl

## 📦 Bestandstypes

| Dataset                    | Inhoud                                                   | Frequentie      | Formaten                      |
|---------------------------|-----------------------------------------------------------|------------------|-------------------------------|
| NPR Statische dataset     | Zonegrenzen, codes, tariefclassificatie per gemeentecode | Bij wijziging    | JSON / CSV / WFS / GeoJSON   |
| NPR Dynamische data       | Dagelijks werkende tarieven per zone                      | Dagelijks        | JSON / API-download           |

## 🔁 Updatefrequentie

- De dynamische dataset wordt **dagelijks vernieuwd**, bruikbaar voor actuele toepassingen (zoals automatische tariefberekening).
- Statische datasets worden bijgewerkt **bij wijzigingen in zone-indeling, gemeentecodes of tariefstructuur**.

## ⚙️ Gebruik: Prijs berekenen per adres + tijdstip

1. Input: Postcode + huisnummer
2. Lookup: Zoek coördinaat of gemeentecode
3. Zoek zone in statische dataset (coördinaatmapping)
4. Raadpleeg dynamische dataset voor tarief op dag + tijd
5. Bereken eindbedrag: `aantal uur × tariefzone`

Je koppelt dus **statische zones** aan **dynamische tariefelementen met tijdschema’s**.

## 📂 Kernonderdelen van de Statische Dataset

### 1. GEBIED
- `AreaId`, `AreaDesc`, `UsageId`, `StartDateArea`, `EndDateArea`

### 2. GEBIEDSBEHEERDER
- `AreaManagerId`, `AreaManagerDesc`, `URL`

### 3. GEBRUIKSDOEL
- Hiërarchische structuur van parkeervormen zoals betaald parkeren, vergunninghouders, blauwe zones etc.

### 4. PARKEERADRES
- Bevat adresinfo (straat, plaats, postcode) van zones of in-/uitgangen

### 5. IN-/UITGANG
- Metadata over voetgangers- en voertuigingangen/uitgangen

### 6. OPENINGSTIJDEN + TOEGANG
- Beschrijft of en wanneer het gebied toegankelijk/open is

### 7. TARIEFBEREKENING
- Tariefstructuren: `FareCalculationCode`, met onderdelen als tijdvak, maximumdagprijs, BTW-percentage

### 8. TARIEFDEEL
- Subdelen van een tarief, met `AmountFarePart`, `StepSizeFarePart`, etc. voor lineaire of bloktarieven

### 9. GPS-COÖRDINATEN en GEOMETRIE
- In WGS84 (EPSG:4326) voor mapping in systemen (GeoJSON/WFS)

## 🔗 Downloads

- **Statische Dataset:** [RDW Opendata – Parkeer Index](https://opendata.rdw.nl/Parkeren/Open-Data-Parkeren-Index-Statisch-en-Dynamisch/f6v7-gjpa)
- **Technische handleiding PDF:** [Beschrijving Datasets NPR (PDF)](https://www.nationaalparkeerregister.nl/-/media/npr/downloads/technische-documentatie/beschrijving-dataset-statische-parkeergegevens.pdf)

## 💡 Let op
- De sleutelvelden zijn aangeduid met `*` in de originele dataset.
- Voor gebruik in je systeem is het aanbevolen deze metadata te parseren naar een database of via een vector-mapping aan adressen te koppelen.

---

Laat me weten als je ook een `.json`-voorbeeld van zo'n zone of tariefelement wil!
