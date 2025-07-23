"""
For now, this class simply writes the PGN to a file (games.pgn) after
each move. This file can be used in combination with the Lichess
broadcaster application.
"""

import env

class LichessBroadcaster:
    def __init__(self):
        return

    def create_broadcast(self, name, description):
        # TODO: Implement more robust Lichess integration. For now, works fine for use with Lichess broadcaster app.
        return True

    def create_round(self, name):
        # TODO: Implement more robust Lichess integration. For now, works fine for use with Lichess broadcaster app.
        return True

    def update_round(self, pgn):
        # TODO: Implement more robust Lichess integration. For now, works fine for use with Lichess broadcaster app.
        print(pgn, file=open(env.PGN_WRITE_LOCATION, "w"), end="\n\n")
