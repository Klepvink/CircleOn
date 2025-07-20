from itertools import count, takewhile
from typing import Iterator
import time

from SquareOffInstance import SquareOffInstance
from GeneralHelpers import *

class ChessBoardUARTHandler:
    def __init__(self, client, rx_char, squareOffInstance: SquareOffInstance, chessboardInstance):
        self.client = client
        self.rx_char = rx_char
        self.squareOffInstance = squareOffInstance
        self.chessboardInstance = chessboardInstance
        self.squareOffInstance.uart_handler = self

    async def CommSuccess(self):
        print("Starting game…")

    async def handle_rx(self, characteristic, data: bytearray):
        decoded = data.decode("utf-8")
        print("received:", decoded)
        if decoded.startswith("0#") and decoded.endswith("u*"):
            square = decoded[2:-2]
            self.squareOffInstance.last_pickup_square = square
            self.squareOffInstance.picked_up_squares.add(square)

        elif decoded.startswith("0#") and decoded.endswith("d*"):
            await self.send_command(b"30#R*\r\n")
            
        elif decoded.startswith("30#") and decoded.endswith("*"):
            new_boardstate = decoded.split('#', 1)[1].rstrip('*')
            print(new_boardstate)
            madeMove = self.squareOffInstance.find_uci_move(new_board_bits=new_boardstate)
            if madeMove:
                self.squareOffInstance._push_and_return(madeMove)

            print(self.chessboardInstance.board)

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