"""
Class that contains all functions needed to play against Lichess.
This is somewhat of a drop-in replacement for the EngineInstance,
but requires access to the SquareOffInstance in order to use the
settings passed from Lichess instead of env.py.
"""
import GeneralHelpers
import chess
import httpx
from threading import Thread
import asyncio

import env

class LichessInstance:
    def __init__(self, chessboardInstance, squareoffInstance):
        self.uart_handler = None
        self.chessboardInstance = chessboardInstance
        self.squareoffInstance = squareoffInstance
        
        self.originalBitboard = "11000011" * 8

        # Lichess specific settings
        self.baseUrl = "https://lichess.org"
        self.gameId = None
        self.opponentColor = None
        self.lichessToken = env.LICHESS_TOKEN
        self.last_seen_move = None

        self.headers = {
            "Authorization": f"Bearer {self.lichessToken}" 
        }

        response = httpx.get(f'{self.baseUrl}/api/account/playing', headers=self.headers)
        ongoingGames = response.json()

        self.mostRecent = ongoingGames['nowPlaying'][0]
        self.gameState = self.mostRecent['fen']
        self.gameId = self.mostRecent['gameId']

        
        self.loop = asyncio.new_event_loop()
        self.move_ready_event = asyncio.Event()
        self.opponentMove = None
        self.moveReady = False

        # Start event loop in background
        Thread(target=self.loop.run_forever, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self.stream_game(), self.loop)

        # Overwrite engine color based on ongoing game.
        if self.mostRecent['color'] == 'white':
            self.opponentColor = 'black'
        else:
            self.opponentColor = 'white'
        self.squareoffInstance.bots = [self.opponentColor]

        # Allow Lichess to overwrite the current chessboardInstance. Not as clean as i'd want it to be as
        # I would rather instantiate the chessboardInstance using the FEN instead of overwriting, but it
        # should work reliably.
        self.chessboardInstance.board = chess.Board(fen=self.gameState)
        self.chessboardInstance.game = chess.pgn.Game.from_board(self.chessboardInstance.board)

        if self.chessboardInstance.board.turn == chess.WHITE:
            self.squareoffInstance.turn = "white"
        elif self.chessboardInstance.board.turn == chess.BLACK:
            self.squareoffInstance.turn = "black"
        
        # TODO: Overwrite written PGN to match game information from Lichess.
        self.chessboardInstance.game.headers['Event'] = env.PGN_EVENT_NAME
        self.chessboardInstance.game.headers['White'] = env.PGN_WHITE_PLAYER
        self.chessboardInstance.game.headers['Black'] = env.PGN_BLACK_PLAYER

        self.chessboardInstance.current_node = self.chessboardInstance.game

    async def wait_for_opponent_move(self):
        current_last_move = self.last_seen_move
    
        while True:
            await self.move_ready_event.wait()
            self.move_ready_event.clear()
    
            if self.last_seen_move != current_last_move:
                return self.last_seen_move
    
            # Spurious wakeup or same move, keep waiting

    
    async def stream_game(self):
        url = f"{self.baseUrl}/api/board/game/stream/{self.gameId}"
    
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=self.headers) as response:
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    data = httpx.Response(200, content=line).json()

                    if data["type"] in ["gameFull", "gameState"]:
                        moves = data.get("state", {}).get("moves") if data["type"] == "gameFull" else data.get("moves")
                        if moves:
                            moves_list = moves.strip().split()
                            if not moves_list:
                                continue
                            
                            # Only look at the *newest* move
                            latest_move = moves_list[-1]
                        
                            # If it's your opponent's turn and it's a new move
                            if (self.mostRecent['color'] == "white" and len(moves_list) % 2 == 0) or \
                               (self.mostRecent['color'] == "black" and len(moves_list) % 2 == 1):
                        
                                if latest_move != self.last_seen_move:
                                    self.opponentMove = latest_move
                                    self.last_seen_move = latest_move
                                    print(f"New opponent move detected: {latest_move}")
                                    self.loop.call_soon_threadsafe(self.move_ready_event.set)
                        
    
    # Is called whenever engine needs to be aware of the new boardstate
    # Boardstate is a valid FEN-string

    def pass_boardstate(self, input_fen=None, input_move=None):
        if input_fen:
            self.chessboardInstance.board.set_fen(input_fen)

        if input_move:
            print(f"{input_move.uci()} was passed to Lichess")
            response = httpx.post(
                f'{self.baseUrl}/api/board/game/{self.gameId}/move/{input_move.uci()}',
                headers=self.headers
            )
            moveResponse = response.json()
            print(moveResponse)

            # Just wait for new move
            future = asyncio.run_coroutine_threadsafe(self.wait_for_opponent_move(), self.loop)
            opponent_uci = future.result()

            print(f"Opponent played: {opponent_uci}")

            # Optional: validate legality only AFTER update
            move = chess.Move.from_uci(opponent_uci)
            if move not in self.chessboardInstance.board.legal_moves:
                print(f"⚠️ Illegal move {opponent_uci} in FEN: {self.chessboardInstance.board.fen()}")
                raise ValueError("Illegal opponent move")

            return opponent_uci


    
    # Function is called to send the move to the chessboardInstance. Should preferably be called from UartComm, as it allows
    # for additional control over what move is ultimately sent to the chessboardInstance. 
    # Input move is UCI-move.
    async def _pass_and_return(self, move):
        if move:
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