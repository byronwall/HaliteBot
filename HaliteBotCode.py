from hlt import *
import logging


class HaliteBotCode:
    def __init__(self, map: GameMap):
        self.map = map
        self.ownedSites = set()
        self.movesThisFrame = []

    def update(self, map: GameMap):
        self.map = map
        # add some other code here as well to update the model
        # TODO check if the map is updated automatically by ref
        # this will called each frame

        logging.debug("reset the moves")
        self.movesThisFrame = []

        logging.debug("update owned sites")
        self.updateListOfOwnedSites()

        logging.debug("update the moves")
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

        framesUntilMove = self.getFramesForStrength(minStrength)

        if framesUntilMove == 0:
            logging.debug("have the strength to take a site, add the moves")

            # loop through owned pieces and make the calls to move them
            for location in self.ownedSites:
                move = self.getNextMove(location, minLocation)

                logging.debug("move to make %s", move)

                if move != None:
                    self.movesThisFrame.append(move)

        return

    def getNextMove(self, start:Location, target: Location) -> Move:

        # this will figure out how to get to the desired location, moving only through owned territory

        # get the desired direction(s)
        northSouth = STILL
        eastWest = STILL

        if start.x < target.x:
            eastWest = EAST
        elif start.x > target.x:
            eastWest = WEST

        if start.y < target.y:
            northSouth = SOUTH
        elif start.y > target.y:
            northSouth = NORTH

        # know the deisred direction, check if either is owned by self
        logging.debug("directions available from %s move %d %d", start, northSouth , eastWest)

        for direction in (northSouth, eastWest):
            if direction != STILL:
                logging.debug("possible direction was not STILL %d", direction)
                site = self.map.getSite(start, direction)

                logging.debug("possible site is owned by us or is the target, move to there")
                # return this move
                return Move(start, direction)

        return None

    def updateListOfOwnedSites(self):

        self.ownedSites = list()

        # this will update the list of sites that are owned by self (will contain locations)
        for x in range(self.map.width):
            for y in range(self.map.height):

                location = Location(x, y)
                site = self.map.getSite(location)

                if site.owner == self.id:
                    self.ownedSites.append(location)
                    logging.debug("added owned site %s with strength %d ", location, self.map.getSite(location).strength)

        return

    def getFramesForStrength(self, strength: int) -> int:
        # this will determine how far out in time is needed to have a total movable strength

        prodTotal = 0
        strengthAvailable = 0

        # get a sum of all the production
        for location in self.ownedSites:
            logging.debug("own that site")
            site = self.map.getSite(location)
            prodTotal += site.production

            logging.debug("owned site at %s", location)
            logging.debug("strengthAvail = %d" % strengthAvailable)
            logging.debug("strength = %d" % site.strength)

            strengthAvailable += site.strength

        logging.debug("info for strength needed %d %d %d" % (strength, strengthAvailable, prodTotal))

        # divide that number by strength desired
        frames = (strength - strengthAvailable) / prodTotal

        return 0 if frames < 0 else frames + 1

    def getBorderOfCurrentSpaces(self) -> set:
        # this will determine the spaces that border the owned pieces
        # iterate through the spaces

        borderSites = set()

        logging.debug("inside the getBorderCall, myID = %d" % self.id)

        mapStr = "\n"

        for y in range(self.map.height):
            for x in range(self.map.width):

                mapChar = "O"
                location = Location(x, y)
                site = self.map.getSite(location)

                # skip if already found or if owned by self
                if (x, y) in borderSites or site.owner == self.id:
                    if site.owner == self.id:
                        logging.debug("border found owned site at %s", location)
                        mapStr += "#"
                    continue

                for direction in DIRECTIONS:
                    # if a neighbor is owned by self, this is a neighbor, add to set
                    if self.map.getSite(location, direction).owner == self.id:
                        borderSites.add((x, y))
                        mapChar = "*"
                        break

                mapStr += mapChar
            mapStr += "\n"
        logging.debug(mapStr)

        # do something with the border sites
        return borderSites
