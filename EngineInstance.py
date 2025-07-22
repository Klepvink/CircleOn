import os
from stockfish import Stockfish
import GeneralHelpers
import chess

class EngineInstance:
    def __init__(self, chessboardInstance):
        self.uart_handler = None
        self.chessboardInstance = chessboardInstance

        self.stockfishPath = os.path.realpath("stockfish.exe")   
        self.stockfish = Stockfish(path=self.stockfishPath, depth=int(4), parameters={
            "Threads": 2, "Minimum Thinking Time": int(4)})
        self.stockfish.set_elo_rating(400)
        self.originalBitboard = "11000011" * 8
    
    def pass_boardstate(self, boardstate):
        self.boardstate = boardstate
        self.stockfish.set_fen_position(boardstate)
        move = self.get_move()
        print(move)
        return move

    def get_move(self):
        if self.boardstate:
            return self.stockfish.get_best_move()
    
    async def _pass_and_return(self, move):
        print(move)

        self.chessboardInstance.board.push_san(move)
        if self.chessboardInstance.current_node is not None:
            self.chessboardInstance.current_node = self.chessboardInstance.current_node.add_variation(move)

        if self.originalBitboard != self.chessboardInstance.board_to_occupation_string():
            diff_squares = GeneralHelpers.bitboard_index_to_squares([i for i in range(len(self.originalBitboard)) if self.originalBitboard[i] != self.chessboardInstance.board_to_occupation_string()[i]])
            await self.uart_handler.send_command(f"25#{"".join(diff_squares)}*".encode())
            diff_squares = []