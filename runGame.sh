#!/bin/bash

BOT_1="python3 MyBot.py --logging -n bw-best-border -T 0.3 -p"
BOT_2="python3 'bots/2017 01 28d, default EAST/MyBot.py' -n prev-best -T 0.3"

SIZE1=40
SIZE2=32

./halite -d "$SIZE1 $SIZE2" "$BOT_1" "$BOT_2" -s 3787688815