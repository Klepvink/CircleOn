from itertools import count, takewhile
from typing import Iterator
import time

from SquareOffInstance import SquareOffInstance
from GeneralHelpers import *

class ChessBoardUARTHandler:
    def __init__(self, client, rx_char, smart_board: SquareOffInstance):
        self.client = client
        self.rx_char = rx_char
        self.smart_board = smart_board
        self.smart_board.uart_handler = self

    async def CommSuccess(self):

        #stop_event = asyncio.Event()

        #async def led_animation():
        #    while not stop_event.is_set():
        #        await self.send_command(b"25#d4d5e4e5*\r\n")
        #        await asyncio.sleep(0.5)
        #        await self.send_command(b"25#c3c4c5c6d3d6e3e6f3f4f5f6*\r\n")
        #        await asyncio.sleep(0.5)
        #        await self.send_command(b"25#b2b3b4b5b6b7c2c7d2d7e2e7f2f7g2g3g4g5g6g7*\r\n")
        #        await asyncio.sleep(0.5)
        #        await self.send_command(b"25#a1a2a3a4a5a6a7a8b1b8c1c8d1d8e1e8f1f8g1g8h1h2h3h4h5h6h7h8*\r\n")
        #        await asyncio.sleep(0.5)

        print("Starting game…")

    async def handle_rx(self, characteristic, data: bytearray):
        decoded = data.decode("utf-8")
        print("received:", decoded)
        if decoded.startswith("0#") and decoded.endswith("u*"):
            square = decoded[2:-2]
            self.smart_board.last_pickup_square = square
            self.smart_board.picked_up_squares.add(square)

        elif decoded.startswith("0#") and decoded.endswith("d*"):
            await self.send_command(b"30#R*\r\n")
            
        elif decoded.startswith("30#") and decoded.endswith("*"):
            new_boardstate = decoded.split('#', 1)[1].rstrip('*')
            print(new_boardstate)
            self.smart_board.find_uci_move(new_board_bits=new_boardstate)
            print(self.smart_board.board)

    async def send_command(self, data: bytes):
        for s in sliced(data, self.rx_char.max_write_without_response_size):
            await self.client.write_gatt_char(self.rx_char, s, response=False)

    async def send_game_start_sequence(self):
        sequence = [b"!#*\r\n", b"25#*\r\n", b"26#ISG*\r\n"]
        for cmd in sequence:
            await self.send_command(cmd)
            time.sleep(0.5)


def sliced(data: bytes, n: int) -> Iterator[bytes]:
    return takewhile(len, (data[i: i + n] for i in count(0, n)))