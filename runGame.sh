#!/bin/bash

BOT_1="python3 MyBot.py"
BOT_2="python3 'bots/2016 12 27, improve prod and timeout/MyBot.py'"

SIZE=30

./halite -d "$SIZE $SIZE" "$BOT_1" "$BOT_2"