from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from sensor.monitor import OTMonitor


BASE = datetime(2026, 10, 20, 10, 0, 0)
attacks = []


# 25 unknown-device cases
for i in range(25):
    attacks.append((
        f"Unknown device {i + 1}",
        "UNKNOWN_DEVICE",
        [{
            "device": f"ROGUE-{i + 1:02d}",
            "source_ip": f"10.10.0.{i + 1}",
            "action": "read",
            "timestamp": BASE + timedelta(minutes=i),
        }],
    ))


# 25 unauthorized-write cases
for i in range(25):
    attacks.append((
        f"Unauthorized write {i + 1}",
        "UNAUTHORIZED_WRITE",
        [{
            "device": ["INV-01", "INV-02", "INV-03"][i % 3],
            "source_ip": f"10.20.0.{i + 1}",
            "action": "write",
            "timestamp": BASE + timedelta(minutes=i),
        }],
    ))


# 25 after-hours configuration-change cases
for i in range(25):
    attacks.append((
        f"After-hours change {i + 1}",
        "OUTSIDE_MAINTENANCE_WINDOW",
        [{
            "device": ["INV-01", "INV-02", "INV-03"][i % 3],
            "source_ip": f"10.30.0.{i + 1}",
            "action": "config_change",
            "timestamp": BASE.replace(hour=22) + timedelta(minutes=i),
        }],
    ))


# 25 traffic-burst cases: five requests within five seconds
for i in range(25):
    start = BASE.replace(hour=11) + timedelta(minutes=i)
    events = [{
        "device": ["INV-01", "INV-02", "INV-03"][i % 3],
        "source_ip": f"10.40.0.{i + 1}",
        "action": "read",
        "timestamp": start + timedelta(seconds=j),
    } for j in range(5)]

    attacks.append((f"Traffic burst {i + 1}", "TRAFFIC_BURST", events))


benign = []
for i in range(50):
    benign.append(({
        "device": ["INV-01", "INV-02", "INV-03"][i % 3],
        "source_ip": f"10.50.0.{i + 1}",
        "action": "read",
        "timestamp": BASE + timedelta(minutes=2 * i),
    }, set()))

for i in range(20):
    benign.append(({
        "device": ["INV-01", "INV-02", "INV-03"][i % 3],
        "source_ip": f"10.51.0.{i + 1}",
        "action": "write",
        "authorized": True,
        "timestamp": BASE.replace(hour=10) + timedelta(minutes=i),
    }, set()))

for i in range(15):
    benign.append(({
        "device": ["INV-01", "INV-02", "INV-03"][i % 3],
        "source_ip": f"10.52.0.{i + 1}",
        "action": "vendor_login",
        "timestamp": BASE.replace(hour=13) + timedelta(minutes=i),
    }, set()))

for i in range(15):
    benign.append(({
        "device": ["INV-01", "INV-02", "INV-03"][i % 3],
        "source_ip": f"10.53.0.{i + 1}",
        "action": "write",
        "authorized": True,
        "timestamp": BASE.replace(hour=22) + timedelta(minutes=i),
    }, {"OUTSIDE_MAINTENANCE_WINDOW"}))


def main():
    detected = 0
    missed = []
    detection_delays = []
    processing_ms = []

    with TemporaryDirectory() as temp:
        print("=== ATTACK EVALUATION: 100 CASES ===")

        for i, (name, expected, events) in enumerate(attacks):
            monitor = OTMonitor(Path(temp) / f"attack-{i}.jsonl")
            first_time = events[0]["timestamp"]
            start_clock = perf_counter()
            found_at = None

            for event in events:
                result = monitor.process_event(event)
                rules = {a["rule"] for a in result["alerts"]}

                if expected in rules:
                    found_at = event["timestamp"]
                    break

            processing_ms.append((perf_counter() - start_clock) * 1000)

            if found_at is not None:
                detected += 1
                detection_delays.append(
                    (found_at - first_time).total_seconds()
                )
            else:
                missed.append(name)

        print(f"Detected: {detected}/100")
        print(f"Missed: {len(missed)}")
        print(f"Detection rate: {detected:.2f}%")
        if missed:
            print("Missed cases:", ", ".join(missed))
        print(
            "Maximum simulated event-to-alert delay: "
            f"{max(detection_delays, default=0):.1f} seconds"
        )
        print(
            "Maximum test-code processing time: "
            f"{max(processing_ms, default=0):.3f} ms"
        )

        monitor = OTMonitor(Path(temp) / "benign.jsonl")
        false_positives = 0
        expected_alert_misses = 0

        print("\n=== BENIGN EVALUATION: 100 CASES ===")
        for i, (event, expected_rules) in enumerate(benign, start=1):
            result = monitor.process_event(event)
            actual_rules = {a["rule"] for a in result["alerts"]}
            unexpected = actual_rules - expected_rules
            missing_expected = expected_rules - actual_rules

            if unexpected:
                false_positives += 1
                print(f"Unexpected alert on case {i}: {sorted(unexpected)}")

            if missing_expected:
                expected_alert_misses += 1
                print(f"Missing expected alert on case {i}: {sorted(missing_expected)}")

        fpr = 100 * false_positives / len(benign)

        print(f"Benign cases: {len(benign)}")
        print(f"Unexpected-alert cases: {false_positives}")
        print(f"Missing expected alerts: {expected_alert_misses}")
        print(f"Observed false-positive rate: {fpr:.2f}%")
        print("\n=== TARGET COMPARISON ===")
        print(
            "Detection target >=95%: "
            f"{'PASS' if detected / len(attacks) >= 0.95 else 'NOT MET'}"
        )
        print(
            "False-positive target <5%: "
            f"{'PASS' if fpr < 5 else 'NOT MET'}"
        )
        print(
            "\nScope: controlled synthetic cases only. "
            "These results do not establish production performance."
        )


if __name__ == "__main__":
    main()
