import os

RADAR_CENTER = (os.environ.get("LAT"), os.environ.get("LONG"))


FLIGHT_DATA_URL = os.environ.get("PIAWARE")


DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 800
FPS = 60


SWEEP_SPEED = 3 
RANGE_RINGS = 5 
MAX_RANGE_KM = 250 


COLORS = {
    'BLACK': (0, 0, 0),
    'GREEN': (0, 255, 0),
    'DARK_GREEN': (0, 100, 0),
    'WHITE': (255, 255, 255),
    'RED': (255, 0, 0),
    'YELLOW': (255, 255, 0)
}

FLIGHT_DATA_UPDATE_INTERVAL = 0.3 
RADAR_UPDATE_INTERVAL = 1.0 / FPS 
