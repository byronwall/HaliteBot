#!/bin/bash

BOT_1="python3 MyBot.py --logging -n bw-complex-adap -T 0.4 -p"
BOT_2="python3 'bots/2017 02 02, less attack options/MyBot.py' -n prev-best -T 0.3"

SIZE1=35
#SIZE2=10

./halite -d "$SIZE1 $SIZE1" "$BOT_1" "$BOT_2"