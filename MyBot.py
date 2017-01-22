import os
import hlt
import logging
import time
import cProfile
import argparse
from HaliteBotCode import *

# set up the command line arguments, will be used for parametric testing
parser = argparse.ArgumentParser(description='Description of your program')

parser.add_argument('-l','--logging', help='Log output from the bot', action="store_true")
parser.add_argument('-p','--profile', help='Profile the bot every 50 cycles', action="store_true")
parser.add_argument('-D','--DISTANCE_THRESHOLD', help='Max distance to count as 1', type=int)
parser.add_argument('-M','--MAX_DISTANCE', help='Max distance to allow move', type=int)
parser.add_argument('-A','--ATTACK_DIST', help='Distance to force attack if available', type=int)
parser.add_argument('-n','--name', help='Bot name')
parser.add_argument('-ga','--GENETIC', help='Do the GA search', action="store_true")

args = vars(parser.parse_args())

# decide if logging should happen
if args["logging"]:
    if not os.path.isdir("logs"):
        os.mkdir("logs")
    LOG_FILENAME = str(int(time.time())) + "-" + '.log'
    logging.basicConfig(filename="logs/" + LOG_FILENAME, level=logging.DEBUG)
else:
    logging.disable(logging.CRITICAL)

myID, gameMap = hlt.get_init()
haliteBot = HaliteBotCode(gameMap, myID, args)

if args["GENETIC"]:
    haliteBot.initialize_strategy()

bot_name = "byronwall-ga1" if args["name"] is None else args["name"]
hlt.send_init(bot_name)

# decide if profiling should happen
SHOULD_PROFILE = args["profile"]
if SHOULD_PROFILE:
    if not os.path.isdir("profiles"):
        os.mkdir("profiles")

frame = 0

while True:

    gameMap.get_frame()

    logging.debug("FRAME START %d", frame)

    should_profile = (myID == 1) and (frame % 50 == 0) and SHOULD_PROFILE
    if should_profile:
        cProfile.run("haliteBot.update(gameMap)", "profiles/profile-" + str(frame) + ".pyprof")
    else:
        haliteBot.update(gameMap)

    moves = haliteBot.moves_this_frame
    logging.debug("moves to make %s", moves)
    hlt.send_frame(moves)

    frame += 1