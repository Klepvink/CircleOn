# CircleOn
CircleOn - Reverse-engineered communicator for the SquareOff Pro chessboard
> [!CAUTION]
> This project is an independent open-source set of scripts and functions for integrating with the SquareOff Pro chessboard via BLE. It is not affiliated with nor endorsed by SquareOff and/or Miko.

## Why?
These scripts were made to provide additional features to the SquareOff Pro chessboard that are not available in the application. It should provide a complete set of features which can be used to play OTB-games, play against Stockfish, fetch live game data for use with third party platforms (such as broadcasting on Lichess) and basic checks to verify the legitimacy of moves.

In it's current form when ran from ```entrypoint.py```, it will do the following:
- Start an over the board game or Stockfish game, depending on the setup in env.py.
- Optionally write the live game to a pgn-file, ready for use with Lichess Broadcaster
- At any point, you are able to enter SquareOff-commands in the terminal for debugging and testing.

## Setup
Before you get started, install the requirements (```python3 -m pip install -r requirements.txt```), and make sure you copy ```env.example.py``` to ```env.py```. You don't actually have to change the contents of this file, but it contains settings for broadcasting your OTB-match to Lichess (using the Lichess Broadcaster app). This is turned off by default. After you've done all that, simply run ```entrypoint.py``` to get started.

## Using the board
When playing chess on the board, there are aome things to pay attention to while playing.
- When moving a piece, pick the piece up and place it on the square you want it to move to. Sliding pieces can introduce false-positives.
- When capturing, pick up both the piece you want to move, and the piece you want to capture, before placing down your moving piece. 
- When castling, move your king first before picking up your rook. The board will indicate where your rook needs to go after. Moving your rook first simply results in a rook move.
- Promotions will be prompted in the terminal.


## Missing features
Right now, ~~playing against an AI is not fully implemented~~, and third party integration was not taken into consideration when writing this. A basic stockfish implementation is included by default (provided by the stockfish python package). If you just want to play OTB, modify the ```env.py``` file. A Windows (.exe) version of Stockfish was used in this repo, however you can modify ```env.py``` to point to a Stockfish binary for your platform.

## Important information
BLEAK (https://github.com/hbldh/bleak )-example code is included in this code, especially a modified version of the ```UART_service.py``` example script. This was done to allow for the testing of commands sent to and from the board. If you run this script without modification, you can directly enter commands to send to the board in your terminal to test functionality.

An LLM was used in order to troubleshoot, write and format parts of this code. A rooted Pixel 3a was used to analyze Bluetooth-data sent to and from the SquareOff application.

## Future plans
Currently, the codebase is a mess due to prototyping and bug fixing, and I want to make sure everything fits in a logical place. I am not a developer by heart, so this may take a sec. Additionally, I am planning on using this code and other observations for a more user-friendly and portable experience for use with the SquareOff Pro board. I find the board to be awesome, but the app is very limited. I ultimately want to implement the ability to play against specific friends on Lichess, broadcast games happening on the board, and play against bots running either locally or on a service like Lichess. In the meantime, I accept contributions if you are interested in adding functionality 🔥 Thanks!
