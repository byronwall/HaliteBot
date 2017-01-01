#!/usr/bin/env python3

for dist_thresh in [3]:
    for max_dist in [9, 11, 13]:
        for attack_dist in [3,5]:
            bot_name = "newest-%d-%d-%d" % (dist_thresh, max_dist, attack_dist)

            add_string = """./manager.py -A "%s" -p "python3 ../bots/newest/MyBot.py -D %d -M %d -A %d -n %s" """ % (
            bot_name, dist_thresh, max_dist, attack_dist, bot_name)

            print(add_string)

