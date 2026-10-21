import asyncio
import logging
import os
from datetime import datetime

from pymodbus import FramerType
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusServerContext,
    ModbusDeviceContext,
    ModbusSequentialDataBlock,
)

from sensor.monitor import OTMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

BIND_HOST = os.getenv("SIM_BIND_HOST", "127.0.0.1")

INVERTERS = [
    {"name": "INV-01", "port": 5020, "power": 5000, "voltage": 230},
    {"name": "INV-02", "port": 5021, "power": 4200, "voltage": 231},
    {"name": "INV-03", "port": 5022, "power": 4800, "voltage": 229},
]

monitor = OTMonitor("logs/events.jsonl")


def make_trace(inverter_name):
    def trace_pdu(sending, pdu):
        # Only process incoming requests, not server responses.
        if sending:
            return pdu

        request_name = type(pdu).__name__
        is_write = "Write" in request_name or "MaskWrite" in request_name

        action = "write" if is_write else "read"

        event = {
            "timestamp": datetime.now(),
            "device": inverter_name,
            "source_ip": "UNKNOWN",
            "action": action,
        }

        record = monitor.process_event(event)

        logging.info(
            "LIVE MODBUS REQUEST | device=%s | request=%s | action=%s | alerts=%s",
            inverter_name,
            request_name,
            action,
            [alert["rule"] for alert in record["alerts"]],
        )

        return pdu

    return trace_pdu


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
        "%s starting at %s:%s",
        inverter["name"],
        BIND_HOST,
        inverter["port"],
    )

    await StartAsyncTcpServer(
        context=context,
        address=(BIND_HOST, inverter["port"]),
        framer=FramerType.SOCKET,
        trace_pdu=make_trace(inverter["name"]),
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
