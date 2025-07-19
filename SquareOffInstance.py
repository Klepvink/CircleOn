import chess
import chess.pgn
import asyncio

class SquareOffInstance:
    def __init__(self, initial_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"):
        self.files = ["A", "B", "C", "D", "E", "F", "G", "H"]
        self.board = chess.Board(fen=initial_fen)
        self.game = chess.pgn.Game.from_board(self.board)
        self.picked_up_squares = set()
        self.current_node = self.game
        self.skip_next_diff = False
        self.uart_handler = None
        self.pgn_export = True

    def reorder_file_major_to_rank_major(self, bitboard_string):
        assert len(bitboard_string) == 64, "Bitboard must be exactly 64 characters"
        squares = [''] * 64
        for file in range(8):
            for rank in range(8):
                src_index = file * 8 + rank
                dst_index = rank * 8 + file
                squares[dst_index] = bitboard_string[src_index]
        return ''.join(squares)

    def find_uci_move(self, new_board_bits):
        if self.skip_next_diff:
            print("Skipping move detection due to castling sync.")
            self.skip_next_diff = False
            return None

        def bitboard_to_set(bits):
            return {i for i, b in enumerate(bits) if b == '1'}

        converted_bits = self.reorder_file_major_to_rank_major(new_board_bits)
        old_occupied = set(chess.SquareSet(self.board.occupied))
        new_occupied = bitboard_to_set(converted_bits)

        moved_from = list(old_occupied - new_occupied)
        moved_to = list(new_occupied - old_occupied)

        print(f"Moved from: {[chess.square_name(sq) for sq in moved_from]}")
        print(f"Moved to: {[chess.square_name(sq) for sq in moved_to]}")

        if len(moved_from) == 1:
            moved_from_square_name = chess.square_name(moved_from[0])
            if moved_from_square_name not in self.picked_up_squares:
                print(f"Blocked move from {moved_from_square_name}: Not picked up.")
                return None

            for move in self.board.legal_moves:
                if move.from_square == moved_from[0]:
                    if len(moved_to) == 1 and move.to_square == moved_to[0]:
                        if self.board.is_capture(move):
                            capture_square_name = chess.square_name(move.to_square)
                            if capture_square_name not in self.picked_up_squares:
                                print(f"Blocked capture on {capture_square_name}: Target not picked up.")
                                continue
                        if self.is_castling_move(move):
                            print("Castling detected, waiting for rook move.")
                            self.skip_next_diff = True
                        return self._push_and_return(move)
                    elif len(moved_to) == 0 and move.to_square in old_occupied:
                        if self.board.is_capture(move):
                            capture_square_name = chess.square_name(move.to_square)
                            if capture_square_name not in self.picked_up_squares:
                                print(f"Blocked capture on {capture_square_name}: Target not picked up.")
                                continue
                        return self._push_and_return(move)

        if len(moved_from) == 2 and len(moved_to) == 1:
            for move in self.board.legal_moves:
                if self.board.is_en_passant(move):
                    if move.to_square == moved_to[0] and move.from_square in moved_from:
                        print("En Passant detected.")
                        return self._push_and_return(move)

        raise ValueError("No legal move found matching diff.")

    def _push_and_return(self, move):
        if self.is_promotion_move(move):
            move.promotion = self.prompt_for_promotion()
        print(f"Matched move: {move.uci()}")
        self.board.push(move)
        if self.current_node is not None:
            self.current_node = self.current_node.add_variation(move)
        asyncio.create_task(self.on_move_made(move.uci()))
        self.picked_up_squares.clear()
        return move.uci()


    # Function called everytime a move is made
    async def on_move_made(self, move):
        if self.board.is_checkmate():
            winner = "Black" if self.board.turn == chess.WHITE else "White"
            print(f"Checkmate! {winner} wins.")
            if self.uart_handler:
                if (winner == "White"):
                    await self.uart_handler.send_command(b"27#wt*\r\n")
                if (winner == "Black"):
                    await self.uart_handler.send_command(b"27#bl*\r\n")
        elif self.board.is_stalemate():
            print("Stalemate. The game is a draw.")
            await self.uart_handler.send_command(b"27#dw*\r\n")
        elif self.board.is_insufficient_material():
            print("Draw due to insufficient material.")
            await self.uart_handler.send_command(b"27#dw*\r\n")

        if self.pgn_export:
            exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
            pgn_text = self.game.accept(exporter)
            print(pgn_text)

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