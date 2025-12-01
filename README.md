# SW5 to Shopify API

Webbasiertes Tool zum Importieren von Artikeln aus Shopware 5 (inkl. Pickware-Zusatzfelder) zu Shopify mit flexiblem Field-Mapping und Daten-Transformationen.

## Features

- Verbindung zu Shopware 5 REST API
- Verbindung zu Shopify Admin API
- Automatisches Auslesen aller verfügbaren Felder aus SW5 Artikeln (inkl. Pickware-Felder)
- Übersicht aller Shopify Produktfelder
- Visuelles Field-Mapping zwischen SW5 und Shopify
- **Transformations-Engine** für Datenmanipulation:
  - Direkte Übernahme (ohne Transformation)
  - String-Ersetzung (einfach oder mit Regex)
  - Split & Join (Delimiter-Konvertierung)
  - Custom Python Code
- Speicherung des Mappings im Browser (LocalStorage)
- Synchronisation einzelner oder aller Artikel
- Unterstützung für Create, Update und Upsert Modi
- Echtzeit-Feedback und Fehlerbehandlung

## Tech-Stack

**Backend:**
- Python 3.8+
- FastAPI
- Requests (für API-Calls)
- Pydantic (Datenvalidierung)

**Frontend:**
- React 18
- TypeScript
- Vite
- Axios
- React Hot Toast (Notifications)

## Schnellstart

Das Projekt enthält ein Start-Script für einfache Inbetriebnahme:

```bash
./start.sh
```

Das Script prüft automatisch:
- Existenz der `.env` Datei (erstellt sie bei Bedarf)
- Installation der Python-Dependencies
- Installation der Node-Dependencies
- Startet Backend und Frontend gleichzeitig

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Node.js 18 oder höher
- Shopware 5 API Zugang (Username + API Key)
- Shopify Admin API Zugang (Access Token)

### Manuelle Installation

#### Backend Setup

1. `.env` Datei im `app/` Verzeichnis erstellen:

```bash
cd app
cp .env.example .env
```

2. `.env` Datei mit API-Credentials ausfüllen:

```env
# Shopware 5 API
SW5_API_URL=https://your-shopware-shop.com/api
SW5_API_USERNAME=your_api_username
SW5_API_KEY=your_api_key

# Shopify API
SHOPIFY_SHOP_URL=your-shop.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_access_token
SHOPIFY_API_VERSION=2024-01

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

3. Python-Dependencies installieren:

```bash
pip install -r requirements.txt
```

4. Backend-Server starten:

```bash
uvicorn main:app --reload --port 8000
```

Das Backend läuft nun auf `http://localhost:8000`

API-Dokumentation: `http://localhost:8000/docs`

#### Frontend Setup

1. Ins Frontend-Verzeichnis wechseln:

```bash
cd frontend
```

2. Node-Dependencies installieren:

```bash
npm install
```

3. Development-Server starten:

```bash
npm run dev
```

Das Frontend läuft nun auf `http://localhost:3000`

## Verwendung

### 1. Verbindung testen

Nach dem Start der Anwendung wird automatisch die Verbindung zu Shopware 5 und Shopify getestet. Grüne Indikatoren zeigen erfolgreiche Verbindungen an.

### 2. Field-Mapping erstellen

Im Bereich "Field Mapping" werden zwei Listen angezeigt:
- **Links:** Alle verfügbaren Shopware 5 Felder (automatisch aus einem Beispiel-Artikel extrahiert)
- **Rechts:** Alle verfügbaren Shopify Produktfelder

**Mapping hinzufügen:**
1. Auf ein SW5-Feld (links) klicken
2. Auf ein Shopify-Feld (rechts) klicken
3. Optional: Transformation bearbeiten (siehe unten)
4. Auf "Mapping hinzufügen" klicken

Das Mapping wird in der Liste "Aktive Mappings" angezeigt und automatisch im Browser gespeichert.

**Beispiel-Mappings:**

| SW5 Feld | Shopify Feld |
|----------|-------------|
| `name` | `title` |
| `descriptionLong` | `body_html` |
| `supplier.name` | `vendor` |
| `mainDetail.number` | `variants[].sku` |
| `mainDetail.prices[0].price` | `variants[].price` |
| `mainDetail.inStock` | `variants[].inventory_quantity` |

### 3. Transformationen anwenden

Für jedes Mapping kann eine Transformation definiert werden, um Daten vor dem Import anzupassen:

#### Transformations-Typen:

**Direkt (direct)**
- Keine Transformation, Wert wird 1:1 übernommen

**Ersetzen (replace)**
- Einfache String-Ersetzung
- Beispiel: "Fahrzeugverwendung:" → "" (entfernen)

**Regex Ersetzen (regex)**
- Pattern-basierte Ersetzung mit regulären Ausdrücken
- Beispiel: `^Fahrzeugverwendung:\s*` → ""

**Split & Join (split_join)**
- Text bei einem Delimiter trennen und mit anderem Delimiter zusammenfügen
- Automatische Entfernung von Präfixen
- Beispiel:
  - **Vorher:** `Fahrzeugverwendung:T3 Bus|Fahrzeugverwendung:T3 Pritsche`
  - **Split Delimiter:** `|`
  - **Join Delimiter:** `, `
  - **Nachher:** `T3 Bus, T3 Pritsche`

**Custom (custom)**
- Eigener Python Code für komplexe Transformationen
- Beispiel: `value.upper()` oder `value.replace('alt', 'neu')`
- ⚠️ **Vorsicht:** Code wird direkt ausgeführt

### 4. Artikel synchronisieren

1. Artikel-IDs eingeben (komma- oder leerzeichengetrennt), z.B. `1, 2, 3` oder `1 2 3`

2. Sync-Modus wählen:
   - **Upsert**: Erstellt neue Produkte oder aktualisiert bestehende (empfohlen)
   - **Create**: Erstellt nur neue Produkte
   - **Update**: Aktualisiert nur bestehende Produkte

3. Auf "Ausgewählte synchronisieren" klicken

4. Fortschritt und Ergebnisse werden in Echtzeit angezeigt

**Tipp:** "Alle Artikel synchronisieren" importiert alle Artikel aus Shopware 5 (Vorsicht bei großen Datenmengen!)

## API-Endpunkte

### Shopware 5

- `GET /api/shopware/test` - Verbindungstest
- `GET /api/shopware/articles` - Artikel auflisten
- `GET /api/shopware/articles/{id}` - Einzelner Artikel
- `GET /api/shopware/fields` - Verfügbare Felder
- `GET /api/shopware/articles/{id}/pickware` - Pickware-Felder eines Artikels

### Shopify

- `GET /api/shopify/test` - Verbindungstest
- `GET /api/shopify/products` - Produkte auflisten
- `GET /api/shopify/products/{id}` - Einzelnes Produkt
- `GET /api/shopify/fields` - Verfügbare Felder
- `POST /api/shopify/products` - Produkt erstellen
- `PUT /api/shopify/products/{id}` - Produkt aktualisieren
- `GET /api/shopify/products/find-by-sku/{sku}` - Produkt per SKU finden

### Mapping

- `POST /api/mapping/transform` - Artikel transformieren (Vorschau)
- `POST /api/mapping/sync` - Artikel synchronisieren
- `GET /api/mapping/validate` - Mapping validieren

## Pickware-Felder

Pickware speichert Zusatzfelder typischerweise im `attribute`-Objekt eines Artikels. Diese Felder werden automatisch erkannt und können gemappt werden.

Beispiel-Pickware-Felder:
- `attribute.pickwareStockManagementStockMovementId`
- `attribute.pickwareErpPurchasePrice`
- Weitere custom attribute fields

## Troubleshooting

### Backend startet nicht

- Alle Dependencies installiert? → `pip install -r requirements.txt`
- `.env` Datei vorhanden und korrekt ausgefüllt?
- API-Verbindungen manuell testen

### Frontend startet nicht

- `node_modules` löschen und `npm install` erneut ausführen
- Port 3000 verfügbar?
- Backend läuft?

### Verbindung zu SW5/Shopify schlägt fehl

**Shopware 5:**
- URL prüfen (Format: `https://your-shop.com/api`)
- Username und API Key prüfen
- API aktiviert?
- Digest Authentication testen

**Shopify:**
- Shop-URL prüfen (Format: `your-shop.myshopify.com`)
- Access Token prüfen
- Richtige API-Scopes aktiviert?
  - `read_products`
  - `write_products`

### Artikel werden nicht korrekt synchronisiert

- Field-Mapping prüfen
- Pflichtfelder gemappt? (z.B. `title`, `variants[].price`)
- Sync-Ergebnisse auf Fehlermeldungen prüfen
- Zunächst mit einzelnen Artikeln testen
- Transformationen korrekt konfiguriert?

## Entwicklung

### Projekt-Struktur

```
sw5-to-shopify-api/
├── app/                        # Backend (FastAPI)
│   ├── api/
│   │   └── routes/
│   │       ├── shopware.py     # SW5 API Routes
│   │       ├── shopify.py      # Shopify API Routes
│   │       └── mapping.py      # Mapping & Sync Logic
│   ├── clients/
│   │   ├── shopware5_client.py # SW5 API Client
│   │   └── shopify_client.py   # Shopify API Client
│   ├── utils/
│   │   └── transformations.py  # Transformation Engine
│   ├── main.py                 # FastAPI App
│   ├── config.py               # Configuration
│   └── requirements.txt
│
├── frontend/                   # Frontend (React + Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConnectionStatus.tsx
│   │   │   ├── FieldMapper.tsx
│   │   │   ├── ProductSync.tsx
│   │   │   └── TransformationEditor.tsx
│   │   ├── utils/
│   │   │   ├── api.ts          # API Client
│   │   │   └── storage.ts      # LocalStorage Helper
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── types.ts
│   └── package.json
│
├── start.sh                    # Start-Script (Unix/Mac)
├── start.bat                   # Start-Script (Windows)
└── README.md
```

### Backend erweitern

Neue API-Routes in `app/api/routes/` hinzufügen und in `main.py` registrieren:

```python
from api.routes import your_new_route

app.include_router(your_new_route.router, prefix="/api/your-route", tags=["Your Route"])
```

### Frontend erweitern

Neue Komponenten in `frontend/src/components/` erstellen und in `App.tsx` importieren.

### Neue Transformations-Typen hinzufügen

Transformations-Logik in `app/utils/transformations.py` erweitern und entsprechende UI in `frontend/src/components/TransformationEditor.tsx` hinzufügen.

## Lizenz

MIT

## Support

Bei Fragen oder Problemen bitte ein Issue auf GitHub erstellen.
