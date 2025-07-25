# Game settings. These settings are used to define how the engine should behave
# when playing against the engine, or to disable engine play altogether.
STARTING_FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

ENGINE_PLAYERS=["white"]
STOCKFISH_LOCATION="stockfish.exe"
ENGINE_ELO=1200

# Experimental, Lichess play
PLAY_LICHESS_GAME = False
LICHESS_TOKEN = ""

# Specific to Lichess broadcasting. This function is handy for when you want to
# stream your OTB-games to your friends, or if you want to perform live analysis
# of your game while you play. This function should be used in combination with
# the Lichess Broadcaster App (https://lichess.org/broadcast/app). Simply point
# the application to the .pgn location, and it should update automatically. You
# could of course technically use the .pgn file to perform analysis using other
# software or websites.
ENABLE_LICHESS_BROADCAST=False
PGN_WRITE_LOCATION="Game/games.pgn"

# General PGN settings. The PGN-string of the ongoing game is always printed to
# the terminal output after a move. Here you can set names of players and event
# names. This information is also passed to the .pgn file that is written when
# Lichess Broadcasting is enabled.
PGN_EVENT_NAME="SquareOff Pro event"
PGN_WHITE_PLAYER="White"
PGN_BLACK_PLAYER="Black"
