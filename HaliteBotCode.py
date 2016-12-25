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
        # self.update_move_targets()

        self.determine_moves_inward()

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

    def determine_moves_inward(self):

        # get the pieces at the border
        edge_squares = self.get_squares_at_the_edge()

        # iterate through those to see which way to go

        # need some criteria to decide what is best
        moves_to_make = dict()  # type: Dict[Square, int]

        # will currently assume the goal is to take the easiest place if available

        # if not enough strength to get there, will call for help instead and remain still
        squares_to_process = set()  # type: Set[Square]
        squares_processed = set()  # type: Set[Square]

        help_needed = dict()  # type: Dict[Square, int]

        for edge_square in edge_squares:
            # get the neighbors, if owned, check if strength is enough to take it
            # if can be taken, make that the move
            squares_processed.add(edge_square)

            for direction, neighbor in enumerate(self.game_map.neighbors(edge_square)):
                if neighbor.owner == self.id:
                    if neighbor in help_needed:
                        if edge_square.strength > help_needed[neighbor]:
                            moves_to_make[edge_square] = direction
                            continue
                    else:
                        squares_to_process.add(neighbor)
                elif edge_square.strength > neighbor.strength:
                    # add the move
                    # this is a crude step to prevent always going for the weak square
                    if neighbor.strength == 0 and random.random() < 0.5:
                        continue

                    moves_to_make[edge_square] = direction
                    if edge_square in help_needed:
                        help_needed.pop(edge_square)
                    break
                else:
                    if neighbor.strength > 0:
                        need = neighbor.strength - edge_square.strength
                        help_needed[edge_square] = need

                            # for the self owned neighbors, add them to a set to process next

        while len(squares_to_process) > 0:
            square_to_process = squares_to_process.pop()

            if square_to_process in squares_processed or square_to_process in moves_to_make:
                continue

            squares_processed.add(square_to_process)

            # check the neighbors of this one, add to the list
            for direction, neighbor in enumerate(self.game_map.neighbors(square_to_process)):
                if neighbor not in squares_processed and neighbor.owner == self.id:
                    squares_to_process.add(neighbor)

                if neighbor in help_needed:
                    need = help_needed[neighbor]
                    logging.debug("current neighbor is in need %d %d", neighbor.x, neighbor.y)
                    if square_to_process.strength > need and neighbor.strength > 0:
                        moves_to_make[square_to_process] = direction
                        help_needed.pop(neighbor)
                        logging.debug("helping that neighbor")
                        break
                    else:
                        # need to pass the buck on help needed
                        help_needed[square_to_process] = need - square_to_process.strength
                        help_needed[neighbor] = need - square_to_process.strength

        # do the processing of the interior ones, only if they are not in the edges also

        # take care of the moves
        for square, direction in moves_to_make.items():
            # skip the move if going to a interior spot too quickly

            if square.strength == 0:
                continue

            target = self.game_map.get_target(square, direction)
            if target.production == 0:
                continue

            if square.strength < square.production * 10:
                continue;

            self.moves_this_frame.append(Move(square, direction))

        return

    def update_move_targets(self):
        # this will go through spaces and find those that are accessible and then ranked by strength
        border_sites = self.get_unowned_border()

        # create a dict to assoc border sites
        border_assoc = dict()  # type: Dict[Square, List[Square]]

        for border_loc in border_sites:
            border_assoc[border_loc] = []

        # loop through owned pieces and make the calls to move them
        for location in self.owned_sites:

            # these are the check to not make moves
            if location.strength < location.production * 10:
                continue

            # find the closest border spot
            min_distance = 1000
            min_location = None
            min_strength = 256

            zero_distance = 1000

            loc_site = self.game_map.get_target(location)

            zero_location = None

            for border_loc in border_sites:
                distance = self.game_map.get_distance(border_loc, location)

                border_strength = border_loc.strength

                if border_strength == 0 and distance < zero_distance:
                    zero_location = border_loc
                    zero_distance = distance
                    continue

                if distance < min_distance or (distance == min_distance and border_strength < min_strength):
                    min_distance = distance
                    min_location = border_loc
                    min_strength = border_loc.strength

            # know the target border site, add to dict
            # allow the zero move if it's the only choice
            if min_location is None and zero_location is not None:
                min_location = zero_location

            # add a check here to see if move should be made
            if min_distance > 4:
                continue

            if min_location is not None and loc_site.strength > 0:
                border_assoc[min_location].append(location)

        # iterate through the border sites now to determine if to move

        for border_loc, locations in border_assoc.items():

            # get the sum of the strengths
            total_strength = 0  # type: int
            for location in locations:
                total_strength += location.strength

            # this random is a step to allow for making a move anyways
            if total_strength > border_loc.strength:
                # if so, move that direction

                for location in locations:
                    move = self.get_next_move(location, border_loc)

                    logging.debug("move to make %s", move)

                    if move is not None:
                        self.moves_this_frame.append(move)

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
