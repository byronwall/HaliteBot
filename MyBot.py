import os

from hlt import *
from networking import *
import logging
import time
from HaliteBotCode import *

myID, gameMap = getInit()
haliteBot = HaliteBotCode(gameMap)
haliteBot.setMyId(myID)
sendInit("byronwall-halite-1")

if not os.path.isdir("logs"):
    os.mkdir("logs")

LOG_FILENAME = str(int(time.time())) + "-" + str(myID) + '.log'
logging.basicConfig(filename="logs/" + LOG_FILENAME, level=logging.DEBUG)

#disbale logging when running on the server
user_name = os.environ.get("USER")
if user_name != "byronwall":
    logging.disable(logging.CRITICAL)

logging.debug('This message should go to the log file')

while True:

    gameMap = getFrame()
    haliteBot.update(gameMap)

    moves = haliteBot.movesThisFrame

    logging.debug("moves to make %s", moves)

    sendFrame(moves)