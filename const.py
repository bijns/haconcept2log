
DOMAIN = "concept2"

# Poll-interval in minuten (kan via Config Flow/Opties worden aangepast)
DEFAULT_UPDATE_INTERVAL_MIN = 30
INTERVAL_MIN = 5
INTERVAL_MAX = 1440

BASE_URL = "https://log.concept2.com"
LOGIN_URL = f"{BASE_URL}/login"

# Alleen de log-pagina bevat de meters
DASHBOARD_CANDIDATES = [
    f"{BASE_URL}/log",
]

# Storage voor baseline en laatste waarden
STORAGE_KEY = f"{DOMAIN}_state"
STORAGE_VERSION = 1

# Sensor keys
SENSOR_LIFETIME = "lifetime_meters"
SENSOR_DAY = "day_meters"
SENSOR_SEASON = "season_meters"
