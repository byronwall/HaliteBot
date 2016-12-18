import random
from typing import Dict
from typing import List

from hlt import *
import logging
from typing import Set


class HaliteBotCode:
    def __init__(self, game_map: GameMap, id: int):
        self.id = id
        self.game_map = game_map
        self.owned_sites = set()
        self.moves_this_frame = []

    def update(self, game_map: GameMap):
        self.game_map = game_map

        logging.debug("reset the moves")
        self.moves_this_frame = []

        logging.debug("update owned sites")
        self.updateListOfOwnedSites()

        logging.debug("update the moves")
        self.updateSiteTarget()

        return

    def updateSiteTarget(self):
        # this will go through spaces and find those that are accessible and then ranked by strength
        border_sites = self.getBorderOfCurrentSpaces()

        # create a dict to assoc border sites
        border_assoc = dict()  # type: Dict[Square, List[Square]]

        for border_loc in border_sites:
            border_assoc[border_loc] = []

        # loop through owned pieces and make the calls to move them
        for location in self.owned_sites:

            # find the closest border spot
            min_distance = 1000
            min_location = None
            min_strength = 256

            loc_site = self.game_map.get_target(location)

            zero_location = None

            for border_loc in border_sites:
                distance = self.game_map.get_distance(border_loc, location)

                # put a threshold on min distance
                if distance <= 2:
                    distance = 0

                border_site = self.game_map.get_target(border_loc)
                border_strength = border_site.strength

                if border_strength == 0:
                    zero_location = border_loc
                    continue

                if distance < min_distance or (distance == min_distance and border_strength < min_strength):
                    min_distance = distance
                    min_location = border_loc
                    min_strength = border_site.strength

                    # know the target border site, add to dict
                    # allow the zero move if it's the only choice
            if min_location is None and zero_location is not None:
                min_location = zero_location

            if min_location is not None and loc_site.strength > 0:
                border_assoc[min_location].append(location)

        # iterate through the border sites now to determine if to move

        for border_loc, locations in border_assoc.items():

            # get the sum of the strengths
            total_strength = 0  # type: int
            for location in locations:
                total_strength += self.game_map.get_target(location).strength

            border_site = self.game_map.get_target(border_loc)

            # this random is a step to allow for making a move anyways
            if total_strength > border_site.strength or random.random() < 0.05:
                # if so, move that direction

                for location in locations:
                    move = self.getNextMove(location, border_loc)

                    logging.debug("move to make %s", move)

                    if move is not None:
                        self.moves_this_frame.append(move)

        return

    def getNextMove(self, start: Square, target: Square) -> Move:

        # this will figure out how to get to the desired location, moving only through owned territory

        # get the desired direction(s), handling the edges
        if start.x == target.x:
            east_west = STILL
        elif start.x < target.x:
            if abs(target.x - start.x) <= self.game_map.width / 2:
                east_west = EAST
            else:
                east_west = WEST
        else:
            if abs(target.x - start.x) <= self.game_map.width / 2:
                east_west = WEST
            else:
                east_west = EAST

        if start.y == target.y:
            north_south = STILL
        elif start.y < target.y:
            if abs(target.y - start.y) <= self.game_map.height / 2:
                north_south = SOUTH
            else:
                north_south = NORTH
        else:
            if abs(target.y - start.y) <= self.game_map.height / 2:
                north_south = NORTH
            else:
                north_south = SOUTH

        # know the deisred direction, check if either is owned by self
        logging.debug("directions available from %s move %d %d", start, north_south, east_west)

        # flip a coin here to see which direction to test first
        if random.random() > 0.5:
            test_directions = (north_south, east_west)
        else:
            test_directions = (east_west, north_south)

        for direction in test_directions:
            if direction != STILL:
                return Move(start, direction)

        return None

    def updateListOfOwnedSites(self):

        self.owned_sites = list()

        # this will update the list of sites that are owned by self (will contain locations)
        for square in self.game_map:
            if square.owner == self.id:
                self.owned_sites.append(square)
                logging.debug("added owned site %s", square)

        return

    def getFramesForStrength(self, strength: int) -> int:
        # this will determine how far out in time is needed to have a total movable strength

        prod_total = 0
        strength_available = 0

        # get a sum of all the production
        for location in self.owned_sites:
            logging.debug("own that site")
            site = self.game_map.get_target(location)
            prod_total += site.production

            logging.debug("owned site at %s", location)
            logging.debug("strengthAvail = %d" % strength_available)
            logging.debug("strength = %d" % site.strength)

            strength_available += site.strength

        logging.debug("info for strength needed %d %d %d" % (strength, strength_available, prod_total))

        # divide that number by strength desired
        if prod_total == 0:
            return 100

        frames = (strength - strength_available) / prod_total

        return 0 if frames < 0 else frames + 1

    def getBorderOfCurrentSpaces(self) -> Set[Square]:
        # this will determine the spaces that border the owned pieces
        # iterate through the spaces

        border_sites = set()

        logging.debug("inside the getBorderCall, myID = %d" % self.id)

        for location in self.game_map:

            # skip if already found or if owned by self
            if (location.x, location.y) in border_sites or location.owner == self.id:
                if location.owner == self.id:
                    logging.debug("border found owned site at %s", location)

                continue

            for neighbor in self.game_map.neighbors(location):
                # if a neighbor is owned by self, this is a neighbor, add to set
                if neighbor.owner == self.id:
                    border_sites.add(location)
                    break

        # do something with the border sites
        return border_sites
