import chess
import chess.pgn
import asyncio

class SquareOffInstance:
    def __init__(self, chessboardInstance):
        self.chessboardInstance = chessboardInstance
        self.picked_up_squares = set()
        self.skip_next_diff = False
        self.uart_handler = None
        self.skip_engine_on_next_move = False

    def reorder_file_major_to_rank_major(self, bitboard_string):
        assert len(bitboard_string) == 64, "Bitboard must be exactly 64 characters"
        squares = [''] * 64
        for file in range(8):
            for rank in range(8):
                src_index = file * 8 + rank
                dst_index = rank * 8 + file
                squares[dst_index] = bitboard_string[src_index]
        return ''.join(squares)

    # Converts bitboard string to a valid uci move
    def find_uci_move(self, new_board_bits):
        if self.skip_next_diff:
            print("Skipping move detection due to castling sync.")
            self.check_engine_turn()
            self.skip_next_diff = False
            return None

        def bitboard_to_set(bits):
            return {i for i, b in enumerate(bits) if b == '1'}

        converted_bits = self.reorder_file_major_to_rank_major(new_board_bits)
        old_occupied = set(chess.SquareSet(self.chessboardInstance.board.occupied))
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

            for move in self.chessboardInstance.board.legal_moves:
                if move.from_square == moved_from[0]:
                    if len(moved_to) == 1 and move.to_square == moved_to[0]:
                        if self.chessboardInstance.board.is_capture(move):
                            capture_square_name = chess.square_name(move.to_square)
                            if capture_square_name not in self.picked_up_squares:
                                print(f"Blocked capture on {capture_square_name}: Target not picked up.")
                                continue

                        if self.chessboardInstance.is_castling_move(move):
                            print("Castling detected, waiting for rook move.")
                            self.skip_engine_on_next_move = True
                            self.skip_next_diff = True
                        return move
                    
                    elif len(moved_to) == 0 and move.to_square in old_occupied:
                        if self.chessboardInstance.board.is_capture(move):
                            capture_square_name = chess.square_name(move.to_square)
                            if capture_square_name not in self.picked_up_squares:
                                print(f"Blocked capture on {capture_square_name}: Target not picked up.")
                                continue
                        return move

        if len(moved_from) == 2 and len(moved_to) == 1:
            for move in self.board.legal_moves:
                if self.board.is_en_passant(move):
                    if move.to_square == moved_to[0] and move.from_square in moved_from:
                        print("En Passant detected.")
                        return move
                    
        raise ValueError("No legal move found matching diff.")

    def _push_and_return(self, move):
        if self.chessboardInstance.is_promotion_move(move):
            move.promotion = self.chessboardInstance.prompt_for_promotion()
        print(f"Matched move: {move.uci()}")
        self.chessboardInstance.board.push(move)
        if self.chessboardInstance.current_node is not None:
            self.chessboardInstance.current_node = self.chessboardInstance.current_node.add_variation(move)
        asyncio.create_task(self.on_move_made(move))
        self.picked_up_squares.clear()
        return move.uci()
    
    def check_engine_turn(self):
        if self.chessboardInstance.board.turn == chess.WHITE:
            print("White's turn")
        elif self.chessboardInstance.board.turn == chess.BLACK:
            print("Black's turn")

    # Function called everytime a move is made
    async def on_move_made(self, move):
        if self.skip_engine_on_next_move:
            print("Skipping engine move after castling rook move.")
            self.skip_engine_on_next_move = False
            return

        if self.chessboardInstance.board.is_checkmate():
            winner = "Black" if self.chessboardInstance.board.turn == chess.WHITE else "White"
            print(f"Checkmate! {winner} wins.")
            if self.uart_handler:
                if (winner == "White"):
                    await self.uart_handler.send_command(b"27#wt*\r\n")
                if (winner == "Black"):
                    await self.uart_handler.send_command(b"27#bl*\r\n")

        elif self.chessboardInstance.board.is_stalemate():
            print("Stalemate. The game is a draw.")
            await self.uart_handler.send_command(b"27#dw*\r\n")
            
        elif self.chessboardInstance.board.is_insufficient_material():
            print("Draw due to insufficient material.")
            await self.uart_handler.send_command(b"27#dw*\r\n")

        if self.chessboardInstance.pgn_export:
            exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
            pgn_text = self.chessboardInstance.game.accept(exporter)
            print(pgn_text)
                    
        self.check_engine_turn()