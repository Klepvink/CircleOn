import asyncio
import sys
from itertools import count, takewhile
from typing import Iterator
from bleak import BleakClient, BleakScanner

from SquareOffInstance import SquareOffInstance
from UartComm import ChessBoardUARTHandler

# UART service UUID's for the SquareOff Pro
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

def sliced(data: bytes, n: int) -> Iterator[bytes]:
    return takewhile(len, (data[i: i + n] for i in count(0, n)))


async def uart_terminal():
    device = await BleakScanner.find_device_by_name("Squareoff Pro", cb={"use_bdaddr": True})

    if device is None:
        print("No matching device found.")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected.")
        for task in asyncio.all_tasks():
            task.cancel()

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, lambda c, d: None)
        print("Connected...")

        nus = client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        smart_board = SquareOffInstance()
        handler = ChessBoardUARTHandler(client, rx_char, smart_board)
        await client.start_notify(UART_TX_CHAR_UUID, handler.handle_rx)
        await handler.send_game_start_sequence()

        loop = asyncio.get_running_loop()
        while True:
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)
            if not data:
                break
            for s in sliced(data, rx_char.max_write_without_response_size):
                await client.write_gatt_char(rx_char, s, response=False)
            print("sent:", data)