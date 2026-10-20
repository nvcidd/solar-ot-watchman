
import asyncio
from datetime import datetime

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient

from config import KNOWN_DEVICES
from sensor.monitor import OTMonitor


async def main():
    name = "INV-01"
    device = KNOWN_DEVICES[name]

    print("Starting unauthorized-write test...")

    client = AsyncModbusTcpClient(
        device["host"],
        port=device["port"],
        framer=FramerType.SOCKET,
    )

    if not await client.connect():
        print("FAIL: Could not connect to INV-01.")
        client.close()
        return

    original_setpoint = None

    try:
        result = await client.read_holding_registers(
            address=0,
            count=3,
            device_id=device["unit_id"],
        )

        if result.isError():
            print(f"FAIL: Initial read failed: {result}")
            return

        original_setpoint = result.registers[2]
        print(f"Original setpoint: {original_setpoint}%")

        write_result = await client.write_register(
            address=2,
            value=75,
            device_id=device["unit_id"],
        )

        if write_result.isError():
            print(f"FAIL: Modbus write failed: {write_result}")
            return

        verify = await client.read_holding_registers(
            address=0,
            count=3,
            device_id=device["unit_id"],
        )

        if verify.isError() or verify.registers[2] != 75:
            print("FAIL: Could not verify the test write.")
            return

        print("PASS: Simulator accepted setpoint 75%")

        monitor = OTMonitor()
        event = monitor.process_event({
            "timestamp": datetime.now(),
            "device": name,
            "source_ip": "127.0.0.1",
            "action": "write",
        })

        detected = any(
            alert["rule"] == "UNAUTHORIZED_WRITE"
            for alert in event["alerts"]
        )

        for alert in event["alerts"]:
            print(
                f'{alert["severity"]} | {alert["rule"]} | '
                f'{alert["message"]}'
            )

        print(
            "PASS: Unauthorized-write rule triggered."
            if detected
            else "FAIL: Unauthorized-write rule did not trigger."
        )

    finally:
        if original_setpoint is not None:
            restore = await client.write_register(
                address=2,
                value=original_setpoint,
                device_id=device["unit_id"],
            )

            if not restore.isError():
                print(
                    f"Cleanup: restored setpoint to "
                    f"{original_setpoint}%"
                )
            else:
                print(
                    f"WARNING: Restoration failed; intended value was "
                    f"{original_setpoint}%."
                )

        client.close()


if __name__ == "__main__":
    asyncio.run(main())
