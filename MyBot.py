from hlt import *
from networking import *
import logging
import time
from HaliteBotCode import *

myID, gameMap = getInit()
haliteBot = HaliteBotCode(gameMap)
haliteBot.setMyId(myID)
sendInit("byronwall-halite-1")

LOG_FILENAME = str(int(time.time())) + "-" + str(myID) + '.log'
logging.basicConfig(filename="logs/" + LOG_FILENAME, level=logging.DEBUG)
logging.debug('This message should go to the log file')

while True:

    gameMap = getFrame()
    haliteBot.update(gameMap)

    moves = haliteBot.movesThisFrame

    logging.debug("moves to make %s", moves)

    sendFrame(moves)