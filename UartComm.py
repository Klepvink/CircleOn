"""
Contains functions which are called on changing states on 
the SquareOff Pro board (pieces being moved, or the state
of the board being communicated). 
"""

import time
import chess
import chess.pgn

import GeneralHelpers

class ChessBoardUARTHandler:
    def __init__(self, client, rx_char, squareOffInstance, chessboardInstance, engineInstance):
        self.client = client
        self.rx_char = rx_char

        self.chessboardInstance = chessboardInstance

        self.squareOffInstance = squareOffInstance
        self.engineInstance = engineInstance

        self.squareOffInstance.uart_handler = self

        # Check if playing against the engine is expected
        if len(self.squareOffInstance.bots) > 0:
            self.squareOffInstance.engineInstance = self.engineInstance
            self.engineInstance.uart_handler = self


    # Function is called on succesful connection to the SquareOff board.
    async def CommSuccess(self):
        print("Starting game…")

    async def handle_rx(self, characteristic, data: bytearray):
        decoded = data.decode("utf-8")
        print("received:", decoded)

        # Called whenever a piece is picked up
        if decoded.startswith("0#") and decoded.endswith("u*"):
            square = decoded[2:-2]

            # Logic is implemented to prevent rare edgecases where multiple moves can share the same
            # occupied space states/bitboard.
            self.squareOffInstance.last_pickup_square = square
            self.squareOffInstance.picked_up_squares.add(square)

        # Called whenever a piece is placed down on the board
        elif decoded.startswith("0#") and decoded.endswith("d*"):

            # Request current state of physical board from SquareOff Pro.
            await self.send_command(b"30#R*\r\n")

        # Triggers in response to current state request 
        elif decoded.startswith("30#") and decoded.endswith("*"):
            new_boardstate = decoded.split('#', 1)[1].rstrip('*')
            
            print(new_boardstate)
            # Communicate the new state of the board as presented by SquareOff to the engine, to allow the engine to light up
            # specific squares on the board.
            self.engineInstance.originalBitboard = new_boardstate

            # Calls the function responsible for converting the SquareOff occupation string to a valid move
            madeMove = await self.squareOffInstance.find_uci_move(new_board_bits=new_boardstate)                

            # madeMove will either return a valid move, or return None in the case of castling (two moves) or illegal moves.
            if madeMove:

                # Push the resulting valid move to the ChessboardInstance.
                # TODO: Move logic from SquareOff class to UartComm
                self.squareOffInstance._push_and_return(madeMove)

            # Check if the physical location of pieces matches with the expected occupied spaces on the ChessboardInstance.
            if (new_boardstate != self.chessboardInstance.board_to_occupation_string()):
                diff_squares = GeneralHelpers.bitboard_index_to_squares([i for i in range(len(new_boardstate)) if new_boardstate[i] != self.chessboardInstance.board_to_occupation_string()[i]])
                print(diff_squares)

                # Light up mismatching LED's on the SquareOff board
                await self.send_command(f"25#{"".join(diff_squares)}*".encode())
                diff_squares = []
            
            # If boardstates are matching (physical and ChessboardInstance, check if game is over). This is done here, to prevent
            # a winner being indicated prematurely.
            if (new_boardstate == self.chessboardInstance.board_to_occupation_string()):
                
                # Debug purposes, print state of the ChessboardInstance
                exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
                pgn_text = self.chessboardInstance.game.accept(exporter)
                print(pgn_text)

                if self.chessboardInstance.board.is_checkmate():
                    winner = "Black" if self.chessboardInstance.board.turn == chess.WHITE else "White"
                    print(f"Checkmate! {winner} wins.")
                    if (winner == "White"):
                        await self.send_command(b"27#wt*\r\n")
                        exit()
                    if (winner == "Black"):
                        await self.send_command(b"27#bl*\r\n")
                        exit()

                elif self.chessboardInstance.board.is_stalemate() or self.chessboardInstance.board.is_insufficient_material():
                    print("The game is a draw.")
                    await self.send_command(b"27#dw*\r\n")
                    exit()
                
                await self.squareOffInstance.on_move_made()

    async def send_command(self, data: bytes):
        for s in GeneralHelpers.sliced(data, self.rx_char.max_write_without_response_size):
            await self.client.write_gatt_char(self.rx_char, s, response=False)

    # Push start of game sequence to the SquareOff board, as intercepted from the SquareOff mobile application
    async def send_game_start_sequence(self):
        sequence = [b"!#*\r\n", b"25#*\r\n", b"26#ISG*\r\n"]
        for cmd in sequence:
            await self.send_command(cmd)
            time.sleep(0.5)