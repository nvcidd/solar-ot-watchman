
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from config import KNOWN_DEVICES

st.set_page_config(
    page_title="Solar OT Watchman",
    page_icon="☀️",
    layout="wide",
)

st.title("☀️ Solar OT Watchman")
st.caption("Local solar-farm OT security monitoring prototype")

# Load events written by the monitor and its tests.
def load_events():
    records = []

    for path in [
        Path("logs/events.jsonl"),
        Path("logs/test_events.jsonl"),
    ]:
        if not path.exists():
            continue

        with path.open("r", encoding="utf-8") as file:
            for line in file:
                try:
                    record = json.loads(line)
                    record["log_source"] = path.name
                    records.append(record)
                except json.JSONDecodeError:
                    continue

    return records


events = load_events()


# Latest telemetry received from the simulated inverters
telemetry_events = [
    event for event in events
    if event.get("event_type") == "modbus_telemetry"
]

latest_readings = {}
for event in telemetry_events:
    device = event.get("device")
    if device and (
        device not in latest_readings
        or event["timestamp"] > latest_readings[device]["timestamp"]
    ):
        latest_readings[device] = event

st.subheader("⚡ Inverter Telemetry")
st.caption("Latest readings collected by the local Modbus poller")

columns = st.columns(len(KNOWN_DEVICES))

for column, device in zip(columns, KNOWN_DEVICES):
    with column:
        st.markdown(f"**{device}**")
        reading = latest_readings.get(device)

        if reading:
            st.metric("Power", f'{reading["power_w"]:,} W')
            st.metric("Voltage", f'{reading["voltage_v"]} V')
            st.metric("Setpoint", f'{reading["setpoint_pct"]}%')
            st.caption(f'Last read: {reading["timestamp"]}')
        else:
            st.warning("Waiting for first reading")


# Device inventory
st.subheader("Device Inventory")

device_rows = [
    {
        "Device": device,
        "Host": details["host"],
        "Modbus TCP Port": details["port"],
        "Unit ID": details["unit_id"],
        "Inventory": "Known device",
    }
    for device, details in KNOWN_DEVICES.items()
]

st.dataframe(
    pd.DataFrame(device_rows),
    use_container_width=True,
    hide_index=True,
)

# Event and alert metrics
st.subheader("Security Overview")

total_events = len(events)
alert_events = sum(bool(event.get("alerts")) for event in events)
total_alerts = sum(len(event.get("alerts", [])) for event in events)

col1, col2, col3 = st.columns(3)
col1.metric("Known Inverters", len(KNOWN_DEVICES))
col2.metric("Events Loaded", total_events)
col3.metric("Alerts Generated", total_alerts)

if not events:
    st.info(
        "No events found yet. Run the detection tests to generate "
        "sample events for the dashboard."
    )
else:
    # Flatten alerts into individual rows.
    alert_rows = []

    for event in events:
        for alert in event.get("alerts", []):
            alert_rows.append({
                "Timestamp": event.get("timestamp", ""),
                "Device": event.get("device", "UNKNOWN"),
                "Source IP": event.get("source_ip", "UNKNOWN"),
                "Rule": alert.get("rule", ""),
                "Severity": alert.get("severity", ""),
                "Details": alert.get("message", ""),
                "Log": event.get("log_source", ""),
            })

    st.subheader("Security Alerts")

    if alert_rows:
        alerts_df = pd.DataFrame(alert_rows)
        st.dataframe(
            alerts_df.sort_values("Timestamp", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No alerts in the loaded event logs.")

    st.subheader("Recent Event History")

    history_rows = [
        {
            "Timestamp": event.get("timestamp", ""),
            "Device": event.get("device", "UNKNOWN"),
            "Source IP": event.get("source_ip", "UNKNOWN"),
            "Action": event.get("action", "unknown"),
            "Alert Count": len(event.get("alerts", [])),
            "Log": event.get("log_source", ""),
        }
        for event in events
    ]

    history_df = pd.DataFrame(history_rows)
    st.dataframe(
        history_df.sort_values("Timestamp", ascending=False).head(50),
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "Prototype note: this dashboard displays recorded events. "
    "It does not yet capture live network packets or verify real-time "
    "inverter availability."
)
