# LURKlandia
Modern LURK server

This LURK server uses a SQLite db to store rooms, room connections, monsters, treasure, and players for game activity.

There are a couple different versions of the program:
1. A single process server, which uses lightweight Python threads to manage the game and player connections. (10-15 players max)
2. A multi-process version which handles each new player connection in its own process. (As many players as yoy have processors for)

Features to come:
Web application with a game-manager dashboard which allows the user to build LURK worlds, add rooms, monsters, and treasure, and rule the LURKiverse!
