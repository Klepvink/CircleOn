"""
Class that contains all functions needed to play against the engine.
This class is able to talk to UartComm directly for LED-control.
"""

import os
from stockfish import Stockfish
import GeneralHelpers
import chess

import env

class EngineInstance:
    def __init__(self, chessboardInstance):
        self.uart_handler = None
        self.chessboardInstance = chessboardInstance
        self.squareoffInstance = None

        # This is now Windows-specific, however I highly encourage you to download your own copy of stockfish (for your own platform) and use that
        self.stockfishPath = os.path.realpath(env.STOCKFISH_LOCATION)   

        # Stockfish init, can be set to any value deemed fit
        self.stockfish = Stockfish(path=self.stockfishPath, depth=20, parameters={
            "Threads": 4, "Minimum Thinking Time": 20})
        
        self.stockfish.set_elo_rating(env.ENGINE_ELO)
        
        self.originalBitboard = "11000011" * 8
    
    # Is called whenever engine needs to be aware of the new boardstate
    # Boardstate is a valid FEN-string

    def pass_boardstate(self, input_fen):
        self.input_fen = input_fen
        self.stockfish.set_fen_position(input_fen)
        if self.input_fen:
            return self.stockfish.get_best_move()
    
    # Function is called to send the move to the chessboardInstance. Should preferably be called from UartComm, as it allows
    # for additional control over what move is ultimately sent to the chessboardInstance. 
    # Input move is UCI-move.
    async def _pass_and_return(self, move):
        print(move)
        # Make change to chessboardInstance
        self.chessboardInstance.board.push_san(move)
        if self.chessboardInstance.current_node is not None:
            self.chessboardInstance.current_node = self.chessboardInstance.current_node.add_variation(chess.Move.from_uci(move))

        # Triggers on mismatch (which should be every move made by the engine)
        if self.originalBitboard != self.chessboardInstance.board_to_occupation_string():

            # As seen in similar functions, indicate differences
            diff_squares = GeneralHelpers.bitboard_index_to_squares([i for i in range(len(self.originalBitboard)) if self.originalBitboard[i] != self.chessboardInstance.board_to_occupation_string()[i]])
            if move:

                # Also append UCI move to LED-control if exists
                diff_squares.append(move)

            # Send LED-command to SquareOff
            await self.uart_handler.send_command(f"25#{"".join(diff_squares)}*".encode())
            diff_squares = []