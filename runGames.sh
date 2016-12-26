#!/bin/bash

BOT_1="python3 MyBot.py"
BOT_2="python3 'opponents/2016 12 18 updated hlt and logic/MyBot.py'"

./halite -d "20 20" "$BOT_1" "$BOT_2"
./halite -d "30 30" "$BOT_1" "$BOT_2"
./halite -d "40 40" "$BOT_1" "$BOT_2"
./halite -d "50 50" "$BOT_1" "$BOT_2"