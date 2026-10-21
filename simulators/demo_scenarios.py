from datetime import datetime, timedelta
from sensor.monitor import OTMonitor


def main():
    monitor = OTMonitor("logs/events.jsonl")
    now = datetime.now()

    scenarios = [
        ("Unknown device", {
            "device": "ROGUE-DEMO-01",
            "source_ip": "10.0.0.99",
            "action": "read",
            "timestamp": now.replace(hour=10, minute=30, second=0,
                                     microsecond=0),
        }, "UNKNOWN_DEVICE"),
        ("Unauthorized write", {
            "device": "INV-01",
            "source_ip": "10.0.0.50",
            "action": "write",
            "timestamp": now.replace(hour=10, minute=31, second=0,
                                     microsecond=0),
        }, "UNAUTHORIZED_WRITE"),
        ("After-hours activity", {
            "device": "INV-02",
            "source_ip": "10.0.0.60",
            "action": "config_change",
            "timestamp": now.replace(hour=22, minute=0, second=0,
                                     microsecond=0),
        }, "OUTSIDE_MAINTENANCE_WINDOW"),
    ]

    for name, event, expected in scenarios:
        result = monitor.process_event(event)
        rules = [a["rule"] for a in result["alerts"]]
        assert expected in rules, f"{name} failed: {rules}"
        print(f"PASS: {name} -> {expected}")

    results = []
    start = now.replace(hour=10, minute=32, second=0, microsecond=0)

    for second in range(5):
        results.append(monitor.process_event({
            "device": "INV-03",
            "source_ip": "10.0.0.70",
            "action": "read",
            "timestamp": start + timedelta(seconds=second),
        }))

    rules = [a["rule"] for a in results[-1]["alerts"]]
    assert "TRAFFIC_BURST" in rules, f"Traffic burst failed: {rules}"
    print("PASS: Traffic burst -> TRAFFIC_BURST")
    print("All four scenarios passed. Synthetic events only.")


if __name__ == "__main__":
    main()
