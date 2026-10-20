
import asyncio
import json
from datetime import datetime
from pathlib import Path

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient

from config import KNOWN_DEVICES

LOG_PATH = Path("logs/events.jsonl")
POLL_INTERVAL = 5


async def poll_inverter(name, details):
    client = AsyncModbusTcpClient(
        details["host"],
        port=details["port"],
        framer=FramerType.SOCKET,
    )

    try:
        if not await client.connect():
            print(f"OFFLINE: {name} — connection failed")
            return

        result = await client.read_holding_registers(
            address=0,
            count=3,
            device_id=details["unit_id"],
        )

        if result.isError():
            print(f"ERROR: {name} — {result}")
            return

        power, voltage, setpoint = result.registers

        event = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "device": name,
            "source_ip": "127.0.0.1",
            "action": "read",
            "power_w": power,
            "voltage_v": voltage,
            "setpoint_pct": setpoint,
            "alerts": [],
            "event_type": "modbus_telemetry",
        }

        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        with LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event) + "\n")

        print(
            f"OK: {name} | Power={power} W | "
            f"Voltage={voltage} V | Setpoint={setpoint}%"
        )

    except Exception as exc:
        print(f"ERROR: {name} — {exc}")

    finally:
        client.close()


async def main():
    print("Solar OT Watchman — Modbus telemetry poller")
    print(f"Polling {len(KNOWN_DEVICES)} inverters every {POLL_INTERVAL}s.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            await asyncio.gather(
                *[
                    poll_inverter(name, details)
                    for name, details in KNOWN_DEVICES.items()
                ]
            )
            await asyncio.sleep(POLL_INTERVAL)

    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTelemetry poller stopped.")
