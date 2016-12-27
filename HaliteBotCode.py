import random
from typing import Dict
from typing import List
from typing import Set
from hlt import *
import logging


class HaliteBotCode:
    def __init__(self, game_map: GameMap, id: int):
        self.id = id
        self.game_map = game_map
        self.owned_sites = set()  # type: Set[Square]
        self.moves_this_frame = []

    def update(self, game_map: GameMap):
        self.game_map = game_map

        logging.debug("reset the moves")
        self.moves_this_frame = []

        logging.debug("update owned sites")
        self.update_owned_sites()

        logging.debug("update the moves")
        self.update_move_targets()

        return

    def get_squares_at_the_edge(self) -> Set[Square]:
        # iterate through all the pieces
        edge_squares = set()

        # add them to a set if 1 of 4 edges is owned by someone other than self
        for square in self.game_map:
            if square.owner != self.id:
                continue

            for neighbor in self.game_map.neighbors(square):
                if neighbor.owner != self.id:
                    edge_squares.add(square)
                    break

        return edge_squares

    def process_moves(self, moves_to_make):

        # this is not used at the moment, need to bring into the fold

        for square, direction in moves_to_make.items():
            # skip the move if going to a interior spot too quickly

            if square.strength == 0:
                continue

            target = self.game_map.get_target(square, direction)
            if target.production == 0:
                continue

            if square.strength < square.production * 10:
                continue

            self.moves_this_frame.append(Move(square, direction))

        return

    def get_square_value(self, square: Square)->float:

        border_values = list()

        # this needs to determine the value of a site, take the average of the
        if square.strength == 0:
            for neighbor in self.game_map.neighbors(square):
                if neighbor.owner != self.id:
                    # TODO adapt this to handle the value metric, works for now
                    border_values.append( self.get_square_metric(neighbor))

        else:
            border_values.append(self.get_square_metric(square))

        if len(border_values) == 0:
            border_values.append(1)

        return min(border_values)

    def get_square_metric(self, square: Square):
        return square.production / (square.strength + 1)

    def update_move_targets(self):
        # this will go through spaces and find those that are accessible and then ranked by strength
        border_sites = self.get_unowned_border()

        # create a dict to assoc border sites
        border_assoc = dict()  # type: Dict[Square, List[Square]]

        for border_square in border_sites:
            border_assoc[border_square] = []

        # loop through owned pieces and make the calls to move them
        for location in self.owned_sites:

            # these are the check to not make moves
            if location.strength < location.production * 10:
                continue

            # find the closest border spot
            min_distance = 1000
            min_location = None
            max_value = 0

            # TODO improve the evaluation metric to consider more than just strength

            for border_square in border_sites:
                distance = self.game_map.get_distance(border_square, location)

                # threshold the distance to allow for some movement
                if distance == 2:
                    distance = 1

                border_value = self.get_square_value(border_square)

                if distance < min_distance or (distance == min_distance and border_value > max_value):
                    min_distance = distance
                    min_location = border_square
                    max_value = border_value

            # add a check here to see if move should be made
            if min_distance > 4:
                continue

            if min_location is not None:
                border_assoc[min_location].append(location)

        # iterate through the border sites now to determine if to move

        for border_square, locations in border_assoc.items():

            # get the sum of the strengths
            total_strength = 0  # type: int
            for location in locations:
                total_strength += location.strength

            if total_strength > border_square.strength:
                # if so, move that direction

                for location in locations:
                    move = self.get_next_move(location, border_square)

                    logging.debug("move to make %s", move)

                    if move is not None:
                        self.moves_this_frame.append(move)

        # TODO improve the move selector to not move to 0 production sites

        return

    def get_next_move(self, start: Square, target: Square) -> Move:

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

    def update_owned_sites(self):

        self.owned_sites = list()

        # this will update the list of sites that are owned by self (will contain locations)
        for square in self.game_map:
            if square.owner == self.id:
                self.owned_sites.append(square)
                logging.debug("added owned site %s", square)

        return

    def get_unowned_border(self) -> Set[Square]:
        # this will determine the spaces that border the owned pieces
        # iterate through the spaces

        border_sites = set()

        logging.debug("inside the getBorderCall, myID = %d" % self.id)

        for location in self.game_map:

            # skip if already found or if owned by self
            if location in border_sites or location.owner == self.id:
                continue

            for neighbor in self.game_map.neighbors(location):
                # if a neighbor is owned by self, this is a neighbor, add to set
                if neighbor.owner == self.id:
                    border_sites.add(location)
                    break

        # do something with the border sites
        return border_sites
