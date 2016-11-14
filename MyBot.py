from hlt import *
from networking import *

myID, gameMap = getInit()
sendInit("byronwall-halite-1")

while True:
    moves = []
    gameMap = getFrame()
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


class HaliteBotCode:
    def __init__(self, map: GameMap):
        self.map = map