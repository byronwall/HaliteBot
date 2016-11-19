from hlt import *
import logging


class HaliteBotCode:
    def __init__(self, game_map: GameMap):
        self.gameMap = game_map
        self.ownedSites = set()
        self.movesThisFrame = []

    def update(self, game_map: GameMap):
        self.gameMap = game_map
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
            site = self.gameMap.getSite(location)

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

                if self.gameMap.getSite(location).strength == 0:
                    # skip a move if no strength
                    continue

                logging.debug("move to make %s", move)

                if move != None:
                    self.movesThisFrame.append(move)

        return

    def getNextMove(self, start:Location, target: Location) -> Move:

        # this will figure out how to get to the desired location, moving only through owned territory

        # get the desired direction(s)
        north_south = STILL
        east_west = STILL

        #these need to handle going around the edge
        if start.x == target.x:
            east_west = STILL
        elif start.x < target.x:
            if abs(target.x - start.x) <= self.gameMap.width / 2:
                east_west = EAST
            else:
                east_west = WEST
        else:
            if abs(target.x - start.x) <= self.gameMap.width / 2:
                east_west = WEST
            else:
                east_west = EAST

        if start.y == target.y:
            north_south = STILL
        elif start.y < target.y:
            if abs(target.y - start.y) <= self.gameMap.height / 2:
                north_south = SOUTH
            else:
                north_south = NORTH
        else:
            if abs(target.y - start.y) <= self.gameMap.height / 2:
                north_south = NORTH
            else:
                north_south = SOUTH

        # know the deisred direction, check if either is owned by self
        logging.debug("directions available from %s move %d %d", start, north_south , east_west)

        #flip a coin here to see which direction to test first
        if random.random() > 0.5:
            test_directions = (north_south, east_west)
        else:
            test_directions = (east_west, north_south)

        for direction in test_directions:
            if direction != STILL:
                return Move(start, direction)

        return None

    def updateListOfOwnedSites(self):

        self.ownedSites = list()

        # this will update the list of sites that are owned by self (will contain locations)
        for x in range(self.gameMap.width):
            for y in range(self.gameMap.height):

                location = Location(x, y)
                site = self.gameMap.getSite(location)

                if site.owner == self.id:
                    self.ownedSites.append(location)
                    logging.debug("added owned site %s with strength %d ", location, self.gameMap.getSite(location).strength)

        return

    def getFramesForStrength(self, strength: int) -> int:
        # this will determine how far out in time is needed to have a total movable strength

        prodTotal = 0
        strengthAvailable = 0

        # get a sum of all the production
        for location in self.ownedSites:
            logging.debug("own that site")
            site = self.gameMap.getSite(location)
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

        for y in range(self.gameMap.height):
            for x in range(self.gameMap.width):

                mapChar = "O"
                location = Location(x, y)
                site = self.gameMap.getSite(location)

                # skip if already found or if owned by self
                if (x, y) in borderSites or site.owner == self.id:
                    if site.owner == self.id:
                        logging.debug("border found owned site at %s", location)
                        mapStr += "#"
                    continue

                for direction in DIRECTIONS:
                    # if a neighbor is owned by self, this is a neighbor, add to set
                    if self.gameMap.getSite(location, direction).owner == self.id:
                        borderSites.add((x, y))
                        mapChar = "*"
                        break

                mapStr += mapChar
            mapStr += "\n"
        logging.debug(mapStr)

        # do something with the border sites
        return borderSites
