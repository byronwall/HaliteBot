from hlt import *
import logging


class HaliteBotCode:
    def __init__(self, map: GameMap):
        self.map = map

    def update(self, map: GameMap):
        self.map = map
        # add some other code here as well to update the model
        # TODO check if the map is updated automatically by ref
        # this will called each frame
        self.updateSiteTarget()

        return

    def setMyId(self, id: int):
        self.id = id
        return

    def updateSiteTarget(self):
        # this will go through spaces and find those that are accessible and then ranked by strength
        borderSites = self.getBorderOfCurrentSpaces()

        # actual max is 255
        minStrength = 256
        minLocation = None

        for (x, y) in borderSites:
            location = Location(x, y)
            site = self.map.getSite(location)

            if site.strength < minStrength:
                minLocation = location
                minStrength = site.strength

        logging.debug("minimum site located at %d,%d" % (minLocation.x, minLocation.y))

        # know where to go, need to figure out how/when to get there

        return

    def getBorderOfCurrentSpaces(self) -> set:
        # this will determine the spaces that border the owned pieces
        # iterate through the spaces

        borderSites = set()

        logging.debug("inside the getBorderCall, myID = %d" % self.id)

        mapStr = "\n"

        for x in range(self.map.width):
            for y in range(self.map.height):
                mapChar = "O"
                location = Location(x, y)
                site = self.map.getSite(location)
                doneWithSite = False

                # skip if already found or if owned by self
                if (x, y) in borderSites or site.owner == self.id:
                    if site.owner == self.id:
                        mapStr += "#"
                    continue

                for direction in DIRECTIONS:
                    # if a neighbor is owned by self, this is a neighbor, add to set
                    if self.map.getSite(location, direction).owner == self.id:
                        borderSites.add((x, y))
                        mapChar = "*"
                        doneWithSite = True
                        break

                mapStr += mapChar
            mapStr += "\n"
        logging.debug(mapStr)

        # do something with the border sites
        return borderSites
