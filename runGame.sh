#!/bin/bash

BOT_1="python3 MyBot.py --logging -n bw-best-border -T 0.2"
BOT_2="python3 'bots/2016 12 30, attempt to force attacks/MyBot.py'"

SIZE=50

./halite -d "$SIZE $SIZE" "$BOT_1" "$BOT_2"