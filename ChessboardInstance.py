import chess
import chess.pgn

class ChessboardInstance:
    def __init__(self, initial_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        self.board = chess.Board(fen=initial_fen)
        self.game = chess.pgn.Game.from_board(self.board)
        self.current_node = self.game
        self.pgn_export = True