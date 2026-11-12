"""Settings for the Lucas County (Toledo) tax delinquent scraper."""
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

# Lucas County Auditor's public ArcGIS layers (lcaudgis / AGOL).
AUD = "https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/"
COLLECTIONS = AUD + "Hosted/AREIS_GENERAL_COLLECTIONS/FeatureServer/0"     # tax balances (annual snapshot)
PARCEL_ADDR = AUD + "LandUse_Zoning/Parcels_Addresses_Generalized_Land_Use_Classification/MapServer/1"  # live owner + mailing
CAMA = ("https://services3.arcgis.com/T8dczfwPixv79EgZ/arcgis/rest/services/"
        "Lucas_County_TaxParcels/FeatureServer/0")                            # value, year built, condition
RENTALS = ("https://services.arcgis.com/2snQ88YUjP9CNEbe/arcgis/rest/services/"
           "Rental_Registry_SEPT_2025/FeatureServer/0")                       # City of Toledo rental registry
AUDITOR_URL = "https://icare.co.lucas.oh.us/LucasCare/search/commonsearch.aspx?mode=parid"

# --- filters (same as Montgomery) ---
MIN_OWED = 1000.0
MIN_YEARS = 2              # years behind as of the snapshot (certified year <= snapshot year - 1)
SKIP_CLASSES = {"E", "U"}  # exempt, utility

STATE_FILE = DATA / "state.json"
RECORDS_FILE = DATA / "records.json"
DASHBOARD_JSON = DOCS / "lucas_tax_delinquent.json"
GHL_CSV = DOCS / "lucas_tax_delinquent_ghl.csv"
REMOVED_KEEP_DAYS = 60
