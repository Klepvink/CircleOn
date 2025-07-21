# CircleOn
CircleOn - Reverse-engineered communicator for the SquareOff Pro chessboard
> [!CAUTION]
> This project is an independent open-source set of scripts and functions for integrating with the SquareOff Pro chessboard via BLE. It is not affiliated with nor endorsed by SquareOff and/or Miko.

## Why?
These scripts were made to provide additional features to the SquareOff Pro chessboard that are not available in the application. Although this script is not made to be used without modification (it is possible from entrypoint.py, but it is purely for troubleshooting and testing commands), it should provide a complete set of features which can be used to play OTB-games, fetch live game data for use with third party platforms (such as broadcasting on Lichess) and basic checks to verify the legitimacy of moves.

In it's current form when ran from entrypoint.py, it will do the following:
- Start an over the board game
- Whenever you make a move, a PGN-string of the current board is printed
- At any point, you are able to enter SquareOff-commands in the terminal

## Missing features
Right now, playing against an AI is not fully implemented, and third party integration was not taken into consideration when writing this. A basic stockfish implementation is included by default. If you just want to play OTB, modify the self.bots list in UartComm.py.

## Important information
BLEAK (https://github.com/hbldh/bleak )-example code is included in this code, especially a modified version of the UART_service.py example script. This was done to allow for the testing of commands sent to and from the board. If you run this script without modification, you can directly enter commands to send to the board in your terminal to test functionality.

AI was used in order to troubleshoot, write and format parts of this code. A rooted Pixel 3a was used to analyze Bluetooth-data sent to and from the SquareOff application.

## Future plans
I am planning on using this code and other observations for a more user-friendly and portable experience for use with the SquareOff Pro board. I find the board to be awesome, but the app is very limited. I ultimately want to implement the ability to play against specific friends on Lichess, broadcast games happening on the board, and play against bots running either locally or on a service like Lichess. In the meantime, I accept contributions if you are interested in adding functionality 🔥 Thanks!
