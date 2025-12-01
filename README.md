# SW5 to Shopify API

Ein webbasiertes Tool zum Importieren von Artikeln aus Shopware 5 (inkl. Pickware-Zusatzfelder) zu Shopify mit flexiblem Field-Mapping.

## Features

- Verbindung zu Shopware 5 REST API
- Verbindung zu Shopify Admin API
- Automatisches Auslesen aller verfügbaren Felder aus SW5 Artikeln (inkl. Pickware-Felder)
- Übersicht aller Shopify Produktfelder
- Visuelles Field-Mapping zwischen SW5 und Shopify
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

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Node.js 18 oder höher
- Shopware 5 API Zugang (Username + API Key)
- Shopify Admin API Zugang (Access Token)

### Backend Setup

1. Erstellen Sie eine `.env` Datei im `app/` Verzeichnis:

```bash
cd app
cp .env.example .env
```

2. Füllen Sie die `.env` Datei mit Ihren API-Credentials aus:

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

3. Installieren Sie die Python-Dependencies:

```bash
pip install -r requirements.txt
```

4. Starten Sie den Backend-Server:

```bash
uvicorn main:app --reload --port 8000
```

Das Backend läuft nun auf `http://localhost:8000`

API-Dokumentation: `http://localhost:8000/docs`

### Frontend Setup

1. Wechseln Sie ins Frontend-Verzeichnis:

```bash
cd frontend
```

2. Installieren Sie die Node-Dependencies:

```bash
npm install
```

3. Starten Sie den Development-Server:

```bash
npm run dev
```

Das Frontend läuft nun auf `http://localhost:3000`

## Verwendung

### 1. Verbindung testen

Nach dem Start der Anwendung wird automatisch die Verbindung zu Shopware 5 und Shopify getestet. Sie sehen grüne Indikatoren, wenn die Verbindungen erfolgreich sind.

### 2. Field-Mapping erstellen

1. Im Bereich "Field Mapping" sehen Sie zwei Listen:
   - Links: Alle verfügbaren Shopware 5 Felder (automatisch aus einem Beispiel-Artikel extrahiert)
   - Rechts: Alle verfügbaren Shopify Produktfelder

2. Klicken Sie auf ein SW5-Feld (links) und dann auf ein Shopify-Feld (rechts)

3. Klicken Sie auf "Mapping hinzufügen"

4. Das Mapping wird in der Liste "Aktive Mappings" angezeigt und automatisch im Browser gespeichert

**Beispiel-Mappings:**

| SW5 Feld | Shopify Feld |
|----------|-------------|
| `name` | `title` |
| `descriptionLong` | `body_html` |
| `supplier.name` | `vendor` |
| `mainDetail.number` | `variants[].sku` |
| `mainDetail.prices[0].price` | `variants[].price` |
| `mainDetail.inStock` | `variants[].inventory_quantity` |

### 3. Artikel synchronisieren

1. Geben Sie Artikel-IDs ein (komma- oder leerzeichengetrennt), z.B. `1, 2, 3` oder `1 2 3`

2. Wählen Sie einen Sync-Modus:
   - **Upsert**: Erstellt neue Produkte oder aktualisiert bestehende (empfohlen)
   - **Create**: Erstellt nur neue Produkte
   - **Update**: Aktualisiert nur bestehende Produkte

3. Klicken Sie auf "Ausgewählte synchronisieren"

4. Sie sehen den Fortschritt und die Ergebnisse in Echtzeit

**Tipp:** Verwenden Sie "Alle Artikel synchronisieren" um alle Artikel aus Shopware 5 zu importieren (Vorsicht bei großen Datenmengen!)

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

Pickware speichert seine Zusatzfelder typischerweise im `attribute`-Objekt eines Artikels. Diese Felder werden automatisch erkannt und können gemappt werden.

Beispiel-Pickware-Felder:
- `attribute.pickwareStockManagementStockMovementId`
- `attribute.pickwareErpPurchasePrice`
- Weitere custom attribute fields

## Troubleshooting

### Backend startet nicht

- Prüfen Sie, ob alle Dependencies installiert sind: `pip install -r requirements.txt`
- Prüfen Sie die `.env` Datei auf korrekte Credentials
- Testen Sie die API-Verbindungen manuell

### Frontend startet nicht

- Löschen Sie `node_modules` und führen Sie `npm install` erneut aus
- Prüfen Sie, ob Port 3000 verfügbar ist
- Prüfen Sie, ob das Backend läuft

### Verbindung zu SW5/Shopify schlägt fehl

**Shopware 5:**
- Prüfen Sie die URL (Format: `https://your-shop.com/api`)
- Prüfen Sie Username und API Key
- Stellen Sie sicher, dass die API aktiviert ist
- Testen Sie mit Digest Authentication

**Shopify:**
- Prüfen Sie die Shop-URL (Format: `your-shop.myshopify.com`)
- Prüfen Sie den Access Token
- Stellen Sie sicher, dass die richtigen API-Scopes aktiviert sind:
  - `read_products`
  - `write_products`

### Artikel werden nicht korrekt synchronisiert

- Prüfen Sie das Field-Mapping
- Achten Sie darauf, dass Pflichtfelder gemappt sind (z.B. `title`, `variants[].price`)
- Prüfen Sie die Sync-Ergebnisse auf Fehlermeldungen
- Testen Sie zunächst mit einzelnen Artikeln

## Entwicklung

### Projekt-Struktur

```
sw5-pickware-import/
├── app/                        # Backend (FastAPI)
│   ├── api/
│   │   └── routes/
│   │       ├── shopware.py     # SW5 API Routes
│   │       ├── shopify.py      # Shopify API Routes
│   │       └── mapping.py      # Mapping & Sync Logic
│   ├── clients/
│   │   ├── shopware5_client.py # SW5 API Client
│   │   └── shopify_client.py   # Shopify API Client
│   ├── main.py                 # FastAPI App
│   ├── config.py               # Configuration
│   └── requirements.txt
│
└── frontend/                   # Frontend (React + Vite)
    ├── src/
    │   ├── components/
    │   │   ├── ConnectionStatus.tsx
    │   │   ├── FieldMapper.tsx
    │   │   └── ProductSync.tsx
    │   ├── utils/
    │   │   ├── api.ts          # API Client
    │   │   └── storage.ts      # LocalStorage Helper
    │   ├── App.tsx
    │   ├── main.tsx
    │   └── types.ts
    └── package.json
```

### Backend erweitern

Fügen Sie neue API-Routes in `app/api/routes/` hinzu und registrieren Sie diese in `main.py`:

```python
from api.routes import your_new_route

app.include_router(your_new_route.router, prefix="/api/your-route", tags=["Your Route"])
```

### Frontend erweitern

Erstellen Sie neue Komponenten in `frontend/src/components/` und importieren Sie diese in `App.tsx`.

## Lizenz

MIT

## Support

Bei Fragen oder Problemen erstellen Sie bitte ein Issue auf GitHub.
