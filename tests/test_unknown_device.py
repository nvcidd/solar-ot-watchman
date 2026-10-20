
from datetime import datetime

from sensor.monitor import OTMonitor


def main():
    print("Starting unknown-device detection test...")

    monitor = OTMonitor("logs/events.jsonl")

    event = monitor.process_event({
        "timestamp": datetime.now(),
        "device": "ROGUE-TEST-01",
        "source_ip": "10.0.0.99",
        "action": "read",
    })

    detected = any(
        alert["rule"] == "UNKNOWN_DEVICE"
        for alert in event["alerts"]
    )

    for alert in event["alerts"]:
        print(
            f'{alert["severity"]} | {alert["rule"]} | '
            f'{alert["message"]}'
        )

    if detected:
        print("PASS: Unknown device detection triggered.")
    else:
        print("FAIL: Unknown device was not detected.")


if __name__ == "__main__":
    main()
