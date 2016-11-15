from hlt import *
import logging

class HaliteBotCode:
    def __init__(self, map: GameMap):
        self.map = map
    def update(self, map:GameMap):
        self.map = map
        #add some other code here as well to update the model
        #TODO check if the map is updated automatically by ref
        #this will called each frame
        self.updateSiteTarget()

        return
    def updateSiteTarget(self):
        #this will go through spaces and find those that are accessible and then ranked by strength
        self.getBorderOfCurrentSpaces()
        return
    def getBorderOfCurrentSpaces(self):
        #this will determine the spaces that border the owned pieces
        #iterate through the spaces

        borderSites = set()

        logging.debug("inside the getBorderCall")

        for y in range(self.map.height):
            for x in range(self.map.width):
                logging.debug("testing border status of %d %d" % (x,y))
                location = Location(x, y)
                site = self.map.getSite(location)
                doneWithSite = False

                #skip if already found or if owned by self
                if (x,y) in borderSites or site.owner == self.map.myID:
                    logging.debug("skipping site")
                    continue

                logging.debug("tested the site, continuing checks")

                for direction in DIRECTIONS:
                    #if a neighbor is owned by self, this is a neighbor, add to set
                    if self.map.getSite(location, direction).owner == self.map.myID:
                        borderSites.add((x,y))
                        logging.debug(str(x) + "," + str(y) + " was added to set")
                        doneWithSite = True
                        break

                #stop checking if a spot was found
                if doneWithSite:
                    break

        #do something with the border sites
        return borderSites