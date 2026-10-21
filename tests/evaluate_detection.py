from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from sensor.monitor import OTMonitor


def main():
    scenarios = [
        {
            "name": "Unknown device",
            "expected": "UNKNOWN_DEVICE",
            "events": [{
                "device": "ROGUE-01",
                "source_ip": "10.0.0.20",
                "action": "read",
                "timestamp": datetime(2026, 10, 20, 10, 0),
            }],
        },
        {
            "name": "Unauthorized write at 02:05",
            "expected": "UNAUTHORIZED_WRITE",
            "events": [{
                "device": "INV-01",
                "source_ip": "10.0.0.30",
                "action": "write",
                "timestamp": datetime(2026, 10, 20, 2, 5),
            }],
        },
        {
            "name": "After-hours configuration change",
            "expected": "OUTSIDE_MAINTENANCE_WINDOW",
            "events": [{
                "device": "INV-02",
                "source_ip": "10.0.0.40",
                "action": "config_change",
                "timestamp": datetime(2026, 10, 20, 22, 0),
            }],
        },
        {
            "name": "Traffic burst",
            "expected": "TRAFFIC_BURST",
            "events": [
                {
                    "device": "INV-03",
                    "source_ip": "10.0.0.50",
                    "action": "read",
                    "timestamp": datetime(2026, 10, 20, 11, 0)
                    + timedelta(seconds=second),
                }
                for second in range(5)
            ],
        },
    ]

    benign_cases = [
        {
            "device": ["INV-01", "INV-02", "INV-03"][i % 3],
            "source_ip": f"10.0.1.{i + 1}",
            "action": "read",
            "timestamp": datetime(2026, 10, 20, 10, 0)
            + timedelta(minutes=i),
        }
        for i in range(20)
    ] + [
        {
            "device": "INV-01",
            "source_ip": "10.0.2.1",
            "action": "write",
            "authorized": True,
            "timestamp": datetime(2026, 10, 20, 10, 30),
        },
        {
            "device": "INV-02",
            "source_ip": "10.0.2.2",
            "action": "write",
            "authorized": True,
            "timestamp": datetime(2026, 10, 20, 22, 30),
            "expected_alerts": ["OUTSIDE_MAINTENANCE_WINDOW"],
        },
    ]

    detected = 0
    missed = 0
    print("=== ATTACK SCENARIOS ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        monitor = OTMonitor(Path(temp_dir) / "evaluation.jsonl")

        for scenario in scenarios:
            matching_alert = None
            events_until_detection = 0

            for index, event in enumerate(scenario["events"], start=1):
                result = monitor.process_event(event)
                rules = [alert["rule"] for alert in result["alerts"]]

                if scenario["expected"] in rules:
                    matching_alert = scenario["expected"]
                    events_until_detection = index
                    break

            if matching_alert:
                detected += 1
                detail = f"detected after event {events_until_detection}"
                status = "PASS"
            else:
                missed += 1
                detail = f"expected {scenario['expected']} was not raised"
                status = "MISS"

            print(f"{status}: {scenario['name']} — {detail}")

        false_alarms = 0
        correctly_clear = 0
        print("\n=== BENIGN EVENTS ===")

        expected_review_alerts = 0
        missing_expected_alerts = 0

        for index, event in enumerate(benign_cases, start=1):
            result = monitor.process_event(event)
            actual = {a["rule"] for a in result["alerts"]}
            expected = set(event.get("expected_alerts", []))
            unexpected = actual - expected
            missing = expected - actual

            if unexpected:
                false_alarms += 1
                print(f"UNEXPECTED ALERT: event {index} — {sorted(unexpected)}")
            elif missing:
                missing_expected_alerts += 1
                print(f"MISSING EXPECTED ALERT: event {index} — {sorted(missing)}")
            elif expected:
                expected_review_alerts += 1
                print(f"PASS: event {index} — expected review alert {sorted(expected)}")
            else:
                correctly_clear += 1

    detection_rate = 100 * detected / len(scenarios)
    false_positive_rate = 100 * false_alarms / len(benign_cases)
    detection_rate = 100 * detected / len(scenarios)
    false_positive_rate = 100 * false_alarms / len(benign_cases)

    print("\n=== SCENARIO-LEVEL SUMMARY ===")
    print(f"Attack scenarios: {len(scenarios)}")
    print(f"Detected scenarios: {detected}")
    print(f"Missed scenarios: {missed}")
    print(f"Scenario detection rate: {detection_rate:.2f}%")
    print(f"Benign and maintenance events: {len(benign_cases)}")
    print(f"Unexpected-alert events: {false_alarms}")
    print(f"Correctly clear events: {correctly_clear}")
    print(f"Unexpected-alert event rate: {false_positive_rate:.2f}%")
    print(
        "\nLimit: Small, controlled synthetic test. "
        "Not a production-performance estimate."
    )


if __name__ == "__main__":
    main()
