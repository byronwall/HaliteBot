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
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
logging.debug('This message should go to the log file')

while True:
    moves = []
    gameMap = getFrame()
    haliteBot.update(gameMap)

    for y in range(gameMap.height):
        for x in range(gameMap.width):
            location = Location(x, y)
            site = gameMap.getSite(location)
            if site.owner == myID:
                if site.strength < site.production * 10:
                    moves.append(Move(location, STILL))
                else:
                    moves.append(Move(location, random.choice(DIRECTIONS)))
    sendFrame(moves)



