import os

INVERTER_HOST = os.getenv("INVERTER_HOST", "127.0.0.1")

KNOWN_DEVICES = {
    "INV-01": {"host": INVERTER_HOST, "port": 5020, "unit_id": 1},
    "INV-02": {"host": INVERTER_HOST, "port": 5021, "unit_id": 1},
    "INV-03": {"host": INVERTER_HOST, "port": 5022, "unit_id": 1},
}

ALLOWED_HOSTS = {"127.0.0.1"}

MAINTENANCE_WINDOW = {
    "start_hour": 9,
    "end_hour": 17,
}

ALERT_RULES = {
    "unknown_device": True,
    "unauthorized_write": True,
    "outside_maintenance_window": True,
    "traffic_burst": True,
}