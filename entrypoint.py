import asyncio
import sys
from bleak import BleakClient, BleakScanner

from GeneralHelpers import UART_SERVICE_UUID, UART_TX_CHAR_UUID, UART_RX_CHAR_UUID, sliced
from SquareOffInstance import SquareOffInstance
from UartComm import ChessBoardUARTHandler
from ChessboardInstance import ChessboardInstance

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

        smart_board = ChessboardInstance()
        initSquareOffInstance = SquareOffInstance(smart_board)
        
        handler = ChessBoardUARTHandler(client, rx_char, squareOffInstance=initSquareOffInstance, chessboardInstance=smart_board)

        await client.start_notify(UART_TX_CHAR_UUID, handler.handle_rx)
        await handler.send_game_start_sequence()

        # First move, check to see who's turn it is
        initSquareOffInstance.check_engine_turn()

        loop = asyncio.get_running_loop()
        while True:
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)
            if not data:
                break
            for s in sliced(data, rx_char.max_write_without_response_size):
                await client.write_gatt_char(rx_char, s, response=False)
            print("sent:", data)

if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        pass
