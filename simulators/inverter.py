import asyncio
import logging

from pymodbus import FramerType
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusServerContext,
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

INVERTERS = [
    {"name": "INV-01", "port": 5020, "power": 5000, "voltage": 230},
    {"name": "INV-02", "port": 5021, "power": 4200, "voltage": 231},
    {"name": "INV-03", "port": 5022, "power": 4800, "voltage": 229},
]


async def run_inverter(inverter):
    store = ModbusDeviceContext(
        hr=ModbusSequentialDataBlock(
            address=1,
            values=[
                inverter["power"],
                inverter["voltage"],
                100,
            ],
        )
    )

    context = ModbusServerContext(
        devices={1: store},
        single=False,
    )

    logging.info(
        "%s starting at 127.0.0.1:%s",
        inverter["name"],
        inverter["port"],
    )

    await StartAsyncTcpServer(
        context=context,
        address=("127.0.0.1", inverter["port"]),
        framer=FramerType.SOCKET,
    )


async def main():
    await asyncio.gather(
        *(run_inverter(inverter) for inverter in INVERTERS)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSolar inverter simulation stopped.")