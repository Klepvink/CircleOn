import chess
import chess.pgn

class ChessboardInstance:
    def __init__(self, initial_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        self.board = chess.Board(fen=initial_fen)
        self.game = chess.pgn.Game.from_board(self.board)
        self.current_node = self.game
        self.pgn_export = True

    def is_promotion_move(self, move):
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN:
            target_rank = chess.square_rank(move.to_square)
            return target_rank == 0 or target_rank == 7
        return False

    def is_castling_move(self, move):
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.KING:
            file_diff = abs(chess.square_file(move.to_square) - chess.square_file(move.from_square))
            return file_diff == 2
        return False

    def prompt_for_promotion(self):
        promotion_map = {
            'q': chess.QUEEN,
            'r': chess.ROOK,
            'b': chess.BISHOP,
            'n': chess.KNIGHT
        }
        while True:
            choice = input("Promote pawn to (q, r, b, n): ").lower()
            if choice in promotion_map:
                return promotion_map[choice]
            print("Invalid choice. Please enter q, r, b, or n.")  
    
    def board_to_occupation_string(self) -> str:
        occupation = ""
        for file in range(8):
            for rank in range(8):
                square = chess.square(file, rank)
                occupation += "1" if self.board.piece_at(square) else "0"
        return occupation
