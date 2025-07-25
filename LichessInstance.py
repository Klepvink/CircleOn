"""
Class that contains all functions needed to play against the engine.
This class is able to talk to UartComm directly for LED-control.
"""

import os
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

        mostRecent = ongoingGames['nowPlaying'][0]

        self.gameId = mostRecent['gameId']

        if mostRecent['color'] == 'white':
            self.opponentColor = 'black'
        else:
            self.opponentColor = 'white'
            self.squareoffInstance.bots = [self.opponentColor]

    
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