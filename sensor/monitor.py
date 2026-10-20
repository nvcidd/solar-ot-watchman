
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
from pathlib import Path

from config import KNOWN_DEVICES, MAINTENANCE_WINDOW


class OTMonitor:
    """Rule-based security monitor for our simulated solar farm."""

    def __init__(self, log_path="logs/events.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.recent_events = defaultdict(deque)

    def process_event(self, event):
        now = event.get("timestamp", datetime.now())
        device = event.get("device", "UNKNOWN")
        source_ip = event.get("source_ip", "UNKNOWN")
        action = event.get("action", "unknown").lower()

        alerts = []

        # Rule 1: Detect unknown devices
        if device not in KNOWN_DEVICES:
            alerts.append({
                "rule": "UNKNOWN_DEVICE",
                "severity": "HIGH",
                "message": f"Unrecognized device: {device}",
            })

        # Rule 2: Detect Modbus writes
        if action in {
            "write",
            "write_single_register",
            "write_multiple_registers",
        }:
            alerts.append({
                "rule": "UNAUTHORIZED_WRITE",
                "severity": "HIGH",
                "message": f"Modbus write observed from {source_ip}",
            })

        # Rule 3: Detect sensitive activity outside maintenance hours
        start = MAINTENANCE_WINDOW["start_hour"]
        end = MAINTENANCE_WINDOW["end_hour"]

        sensitive_actions = {
            "write",
            "write_single_register",
            "write_multiple_registers",
            "vendor_login",
            "config_change",
        }

        if (
            (now.hour < start or now.hour >= end)
            and action in sensitive_actions
        ):
            alerts.append({
                "rule": "OUTSIDE_MAINTENANCE_WINDOW",
                "severity": "MEDIUM",
                "message": (
                    f"Sensitive activity at {now:%H:%M} "
                    "outside maintenance hours"
                ),
            })

        # Rule 4: Detect five or more events within ten seconds
        history = self.recent_events[source_ip]
        cutoff = now - timedelta(seconds=10)

        while history and history[0] < cutoff:
            history.popleft()

        history.append(now)

        if len(history) >= 5:
            alerts.append({
                "rule": "TRAFFIC_BURST",
                "severity": "MEDIUM",
                "message": f"{len(history)} events within ten seconds",
            })

        record = {
            "timestamp": now.isoformat(),
            "device": device,
            "source_ip": source_ip,
            "action": action,
            "alerts": alerts,
        }

        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

        return record
