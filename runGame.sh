#!/bin/bash

BOT_1="python3 MyBot.py -n current-2-3 --D 2 --M 3"
BOT_2="python3 'bots/2016 12 27, improve prod and timeout/MyBot.py'"

SIZE=20

./halite -d "$SIZE $SIZE" "$BOT_1" "$BOT_2"