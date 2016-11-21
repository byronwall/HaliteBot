import os

from hlt import *
from networking import *
import logging
import time
from HaliteBotCode import *
import cProfile

myID, gameMap = getInit()
haliteBot = HaliteBotCode(gameMap, myID)

sendInit("byronwall-halite-1")

if not os.path.isdir("logs"):
    os.mkdir("logs")

if not os.path.isdir("profiles"):
    os.mkdir("profiles")

SHOULD_PROFILE = False

LOG_FILENAME = str(int(time.time())) + "-" + str(myID) + '.log'
logging.basicConfig(filename="logs/" + LOG_FILENAME, level=logging.DEBUG)

#disbale logging when running on the server
user_name = os.environ.get("USER")
if user_name != "byronwall":
    logging.disable(logging.CRITICAL)
else:
    SHOULD_PROFILE = True

logging.debug('This message should go to the log file')
frame = 1

while True:

    gameMap = getFrame()

    should_profile = (myID == 1) and (frame % 50 == 0) and SHOULD_PROFILE

    if should_profile:
        cProfile.run("haliteBot.update(gameMap)", "profiles/profile-" + str(frame) + ".pyprof")
    else:
        haliteBot.update(gameMap)

    moves = haliteBot.moves_this_frame

    logging.debug("moves to make %s", moves)

    sendFrame(moves)
    frame += 1