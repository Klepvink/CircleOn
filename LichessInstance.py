"""
Class that contains all functions needed to play against Lichess.
This is somewhat of a drop-in replacement for the EngineInstance,
but requires access to the SquareOffInstance in order to use the
settings passed from Lichess instead of env.py.
"""
import GeneralHelpers
import chess
import requests

import env

class LichessInstance:
    def __init__(self, chessboardInstance):
        self.uart_handler = None
        self.chessboardInstance = chessboardInstance
        self.squareoffInstance = None
        
        self.originalBitboard = "11000011" * 8

        # Lichess specific settings
        self.baseUrl = "https://lichess.org"
        self.gameId = None
        self.opponentColor = None
        self.lichessToken = env.LICHESS_TOKEN

        self.headers = {
            "Authorization": f"Bearer {self.lichessToken}" 
        }

        ongoingGames = requests.get(f'{self.baseUrl}/api/account/playing', headers=self.headers).json()

        # Not ideal, but selecting the most recent game works for now.
        # TODO: Add game selector
        mostRecent = ongoingGames['nowPlaying'][0]
        self.gameState = mostRecent['fen']
        self.gameId = mostRecent['gameId']

        # Overwrite engine color based on ongoing game.
        if mostRecent['color'] == 'white':
            self.opponentColor = 'black'
        else:
            self.opponentColor = 'white'
        self.squareoffInstance.bots = [self.opponentColor]

        # Allow Lichess to overwrite the current chessboardInstance. Not as clean as i'd want it to be as
        # I would rather instantiate the chessboardInstance using the FEN instead of overwriting, but it
        # should work reliably.
        self.chessboardInstance.board = chess.Board(fen=self.gameState)
        self.chessboardInstance.game = chess.pgn.Game.from_board(self.chessboardInstance.board)

        # TODO: Overwrite written PGN to match game information from Lichess.
        self.chessboardInstance.game.headers['Event'] = env.PGN_EVENT_NAME
        self.chessboardInstance.game.headers['White'] = env.PGN_WHITE_PLAYER
        self.chessboardInstance.game.headers['Black'] = env.PGN_BLACK_PLAYER

        self.chessboardInstance.current_node = self.chessboardInstance.game
    
    # Is called whenever engine needs to be aware of the new boardstate
    # Boardstate is a valid FEN-string

    def pass_boardstate(self, input_fen):
        return
    
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