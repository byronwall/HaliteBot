#!/bin/bash

BOT_1="python3 MyBot.py"
BOT_2="python3 'bots/2016 12 30, attempt to force attacks/MyBot.py'"

SIZE=30

./halite -q -d "$SIZE $SIZE" "$BOT_1" "$BOT_2"