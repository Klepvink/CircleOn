"""
Contains logic for parsing SquareOff events, and
preventing false positives.
"""

import chess
import asyncio

import GeneralHelpers as GeneralHelpers 
import env

class SquareOffInstance:
    def __init__(self, chessboardInstance):
        self.chessboardInstance = chessboardInstance
        self.uart_handler = None

        # By default, don't use the engine if not needed
        self.engineInstance = None

        # Assuming default bitboard unless explicitely set
        self.bitboardState = "11000011" * 8
        self.picked_up_squares = set()

        self.skip_next_diff = False
        self.set_castling_move = False
        self.turn = "white"

        if env.PLAY_LICHESS_GAME:    
            self.bots = []
        self.bots = env.ENGINE_PLAYERS

    async def lightNonmatchingSquares(self, new_boardstate):
        if not self.set_castling_move:
            await asyncio.sleep(0.3)
            await self.uart_handler.send_command(b"26#ISR*")
            await asyncio.sleep(0.3)
    
        diff_squares = GeneralHelpers.bitboard_index_to_squares([i for i in range(len(new_boardstate)) if new_boardstate[i] != self.chessboardInstance.board_to_occupation_string()[i]])
        print(diff_squares)

        # Light up mismatching LED's on the SquareOff board
        await self.uart_handler.send_command(f"25#{"".join(diff_squares)}*".encode())
        diff_squares = []

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
    async def find_uci_move(self, new_board_bits):
        self.bitboardState = new_board_bits
        if self.skip_next_diff:
            print("Skipping move detection due to castling sync.")

            if new_board_bits != self.chessboardInstance.board_to_occupation_string():
                await self.lightNonmatchingSquares(new_board_bits)
            
            self.skip_next_diff = False

            # Check turn, pass queued castling move
            await self.check_turn(move=self.set_castling_move)

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
                            self.set_castling_move = move
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
            for move in self.chessboardInstance.board.legal_moves:
                if self.chessboardInstance.board.is_en_passant(move):
                    if move.to_square == moved_to[0] and move.from_square in moved_from:
                        print("En Passant detected.")
                        return move

        if self.turn in self.bots:
            print(f"Bot turn for {self.turn}, not taken into consideration as player move")
            return
        
        print("No legal move found matching diff.")
        return None

    def _push_and_return(self, move):
        if self.chessboardInstance.is_promotion_move(move):
            move.promotion = self.chessboardInstance.prompt_for_promotion()
        print(f"Matched move: {move.uci()}")

        self.chessboardInstance.board.push(move)
        if self.chessboardInstance.current_node is not None:
            self.chessboardInstance.current_node = self.chessboardInstance.current_node.add_variation(move)

        self.picked_up_squares.clear()

        return move.uci()
    
    async def check_turn(self, move=None):
        if self.chessboardInstance.board.turn == chess.WHITE:
            self.turn = "white"
            print("White's turn")
        elif self.chessboardInstance.board.turn == chess.BLACK:
            self.turn = "black"
            print("Black's turn")

        if len(self.bots) > 0 and self.turn in self.bots:
            # Make bot move
            engineMove = self.engineInstance.pass_boardstate(input_fen=self.chessboardInstance.board.fen(), input_move=move)
            await self.engineInstance._pass_and_return(engineMove)
            
    # Function called everytime a move is made
    async def on_move_made(self, move: None):
        if self.set_castling_move:
            print("Skipping engine move after castling rook move.")
            self.set_castling_move = False

        await self.check_turn(move=move)