import asyncio
import sys
from bleak import BleakClient, BleakScanner

# CircleOn specific imports, such as helper functions and the python-chess instance
from GeneralHelpers import UART_SERVICE_UUID, UART_TX_CHAR_UUID, UART_RX_CHAR_UUID, sliced
from UartComm import ChessBoardUARTHandler

# General settings for the application
import env

async def uart_terminal():

    # Squareoff Pro should be a safe hard-coded value
    device = await BleakScanner.find_device_by_name("Squareoff Pro", cb={"use_bdaddr": True})

    if device is None:
        print("No matching device found.")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected.")
        for task in asyncio.all_tasks():
            task.cancel()

    async with BleakClient(address_or_ble_device=device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, lambda c, d: None)
        print("Connected...")

        nus = client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        # Instantiate the UART communicator, responsible for performing activities with changes on the board
        handler = ChessBoardUARTHandler(client=client, rx_char=rx_char)

        await client.start_notify(UART_TX_CHAR_UUID, handler.handle_rx)
        
        await handler.start_game()

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
