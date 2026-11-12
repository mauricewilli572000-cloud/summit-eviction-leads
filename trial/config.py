"""Settings for the Toledo (Lucas County, OH) code enforcement lead scraper."""
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

TOLEDO = "https://gis.toledo.oh.gov/arcgis/rest/services/"
SERVICE_REQUESTS = TOLEDO + "Public/CityWorks_ServiceRequest_2022/MapServer/1"   # resident complaints (daily)
MOWING = TOLEDO + "Grass_Mowing_Program/MapServer/0"                             # parcels the city mows
DEMOS = TOLEDO + "Demolition_Map_MIL1/MapServer/0"                               # active & planned demolitions
PARCEL_ADDR = ("https://lcaudgis.co.lucas.oh.us/gisaudserver/rest/services/LandUse_Zoning/"
               "Parcels_Addresses_Generalized_Land_Use_Classification/MapServer/1")  # owner + mailing
AUDITOR_URL = "https://icare.co.lucas.oh.us/LucasCare/Datalets/Datalet.aspx?sIndex=0&idx=1&UseSearch=no&pin={pin}"

# Complaint types that point at a neglected property, and their base points.
REQUEST_TYPES = {
    "Trespasssing in Vacant Structure or House": ("Vacant house (trespassing)", 30),   # sic: city's spelling
    "Structure Concern (Property Maintenance, Vehicles)": ("Structure / property maintenance", 20),
    "Blight Concern (Debris, Trash, or Dumping)": ("Blight (debris / trash)", 15),
    "Drug Activity or Drug House Concern": ("Drug house complaint", 15),
    "High Grass Concern": ("High grass", 10),
}
MOWING_POINTS = 25           # the city mows it because the owner doesn't (code enforcement funded)
DEMO_POINTS = 40             # on the city's active / planned demolition list
LOOKBACK_DAYS = 180          # complaints filed in this window
OPEN_DAYS = 90               # a closed complaint still counts as recent for this long

DASHBOARD_JSON = DOCS / "toledo_code_enforcement.json"
GHL_CSV = DOCS / "ghl_toledo_code_enforcement.csv"
STATE_FILE = DATA / "state.json"   # first-seen dates per lead
