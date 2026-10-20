import asyncio

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient


INVERTERS = [
    {"name": "INV-01", "port": 5020, "power": 5000, "voltage": 230},
    {"name": "INV-02", "port": 5021, "power": 4200, "voltage": 231},
    {"name": "INV-03", "port": 5022, "power": 4800, "voltage": 229},
]


async def test_inverter(inverter):
    client = AsyncModbusTcpClient(
        "127.0.0.1",
        port=inverter["port"],
        framer=FramerType.SOCKET,
    )

    try:
        if not await client.connect():
            print(f"FAIL: {inverter['name']} connection failed")
            return False

        result = await client.read_holding_registers(
            address=0,
            count=3,
            device_id=1,
        )

        if result.isError():
            print(f"FAIL: {inverter['name']} read failed: {result}")
            return False

        power, voltage, setpoint = result.registers

        print(
            f"PASS: {inverter['name']} | "
            f"Power={power} W | Voltage={voltage} V | "
            f"Setpoint={setpoint}%"
        )
        return True

    except Exception as exc:
        print(f"FAIL: {inverter['name']} | {exc}")
        return False

    finally:
        client.close()


async def main():
    results = await asyncio.gather(
        *(test_inverter(inverter) for inverter in INVERTERS)
    )

    print(f"\nConnectivity: {sum(results)}/{len(results)} inverters passed.")


if __name__ == "__main__":
    asyncio.run(main())