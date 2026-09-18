from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

OSM_PATH = PROJECT_ROOT / "data/raw/osm/hyderabad_drive.graphml"
HMRL_DIR = PROJECT_ROOT / "data/raw/hmrl_gtfs_sep2026"
TGSRTC_DIR = PROJECT_ROOT / "data/raw/tgsrtc_gtfs_jun2026"
MMTS_DIR = PROJECT_ROOT / "data/raw/Open_Data_MMTS_Hyd"

METRO_INTEL_PATH = PROJECT_ROOT / "data/processed/metro_station_intelligence.csv"
HUB_PATH = PROJECT_ROOT / "data/processed/multimodal_hubs.csv"

OUTPUT_PATH = PROJECT_ROOT / "outputs/mobility_atlas.html"
TEMPLATE_PATH = Path(__file__).resolve().parent / "template.html"

# Official HMRL line colours (routes.txt uses these without leading #).
METRO_COLORS = {
    "RED": "#E31E24",
    "GREEN": "#009846",
    "BLUE": "#007ABB",
}

METRO_LINE_NAMES = {
    "RED": "Red Line",
    "GREEN": "Green Line",
    "BLUE": "Blue Line",
}

MAP_CENTER = (17.405, 78.475)
MAP_ZOOM = 11
