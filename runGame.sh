#!/bin/bash

BOT_1="python3 MyBot.py"
BOT_2="python3 'bots/2016 12 29, start overkill/MyBot.py'"

SIZE=20

./halite -q -d "$SIZE $SIZE" "$BOT_1" "$BOT_2"