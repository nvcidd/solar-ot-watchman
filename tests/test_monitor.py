
from datetime import datetime, timedelta

from sensor.monitor import OTMonitor


def main():
    monitor = OTMonitor("logs/test_events.jsonl")

    # Test 1: Normal read during maintenance hours
    normal = monitor.process_event({
        "device": "INV-01",
        "source_ip": "10.0.0.10",
        "action": "read",
        "timestamp": datetime(2026, 10, 20, 10, 0, 0),
    })

    assert normal["alerts"] == []
    print("PASS: Normal read produces no alerts.")

    # Test 2: Unknown device
    unknown = monitor.process_event({
        "device": "ROGUE-01",
        "source_ip": "10.0.0.20",
        "action": "read",
        "timestamp": datetime(2026, 10, 20, 10, 1, 0),
    })

    assert any(a["rule"] == "UNKNOWN_DEVICE" for a in unknown["alerts"])
    print("PASS: Unknown device detected.")

    # Test 3: Modbus write event
    write = monitor.process_event({
        "device": "INV-01",
        "source_ip": "10.0.0.30",
        "action": "write",
        "timestamp": datetime(2026, 10, 20, 10, 2, 0),
    })

    assert any(a["rule"] == "UNAUTHORIZED_WRITE" for a in write["alerts"])
    print("PASS: Write event flagged.")

    # Test 4: Activity outside maintenance hours
    after_hours = monitor.process_event({
        "device": "INV-01",
        "source_ip": "10.0.0.40",
        "action": "config_change",
        "timestamp": datetime(2026, 10, 20, 22, 0, 0),
    })

    assert any(
        a["rule"] == "OUTSIDE_MAINTENANCE_WINDOW"
        for a in after_hours["alerts"]
    )
    print("PASS: Out-of-hours activity detected.")

    # Test 5: Five events within ten seconds
    burst_results = []

    for second in range(5):
        burst_results.append(monitor.process_event({
            "device": "INV-01",
            "source_ip": "10.0.0.50",
            "action": "config_change",
            "timestamp": datetime(2026, 10, 20, 11, 0, 0)
            + timedelta(seconds=second),
        }))

    assert any(
        a["rule"] == "TRAFFIC_BURST"
        for a in burst_results[-1]["alerts"]
    )
    print("PASS: Traffic burst detected.")

    print("\nAll five detection tests passed.")


if __name__ == "__main__":
    main()
