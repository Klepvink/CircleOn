from itertools import count, takewhile
from typing import Iterator

# UART service UUID's for the SquareOff Pro
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHAR_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

def sliced(data: bytes, n: int) -> Iterator[bytes]:
    return takewhile(len, (data[i: i + n] for i in count(0, n)))

def bitboard_index_to_squares(bitboard_indexes):
    squares = []
    for i in bitboard_indexes:
        letter = list(map(chr, range(97, 105)))[i // 8]
        number = (i % 8) + 1
        squares.append(f"{letter}{number}")
    return squares