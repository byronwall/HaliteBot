import random
from typing import Dict
from typing import List
from typing import Set
from hlt import *
import logging

from collections import defaultdict
from heapq import *

Edge = namedtuple('Edge', 'left right')

Path = namedtuple('Path', 'value prod_avail time_to_reach steps')

class HaliteBotCode:
    def __init__(self, game_map: GameMap, id: int, options=defaultdict(None)):
        self.id = id
        self.game_map = game_map
        self.owned_sites = set()  # type: Set[Square]
        self.moves_this_frame = []
        self.time_at_square = dict()  # type: Dict[Square, int]
        self.expected_strength = dict()  # type: Dict[Square, int]
        self.frame = 0

        self.DISTANCE_THRESHOLD = 3 if options["DISTANCE_THRESHOLD"] is None else options["DISTANCE_THRESHOLD"]
        self.MAX_DISTANCE = 9 if options["MAX_DISTANCE"] is None else options["MAX_DISTANCE"]
        self.ATTACK_DIST = 3 if options["ATTACK_DIST"] is None else options["ATTACK_DIST"]

        for square in self.game_map:
            self.time_at_square[square] = 0

    def update(self, game_map: GameMap):
        self.game_map = game_map

        logging.debug("reset the moves")
        self.moves_this_frame = []

        logging.debug("update owned sites")
        self.update_owned_sites()

        logging.debug("update the moves")
        self.update_move_targets()

        self.frame += 1

        return

    def can_move_from(self, source: Square):
        # must stay at spot to build strength
        allow_move = True

        if source.strength < source.production * 5:
            allow_move = False

        return allow_move

    def is_move_allowed(self, move: Move) -> bool:

        allow_move = True

        source = move.square
        target = self.game_map.get_target(source, move.direction)

        # must stay for one turn to avoid constantly moving
        # if self.time_at_square[source] <= 1:
        #    allow_move = False

        # this should prevent large blocks from combining
        if allow_move:
            if 280 - self.expected_strength[target] < source.strength:
                allow_move = False
            else:
                self.expected_strength[target] += source.strength
                self.expected_strength[source] -= source.strength

        return allow_move

    def can_attack_square(self, square: Square) -> bool:
        # this will return a bool indicating if the square can be attacked
        return any(neighbor.owner not in [0, self.id] for neighbor in self.game_map.neighbors(square))

    def get_square_value(self, square: Square) -> float:

        border_value = 1000000

        # this needs to determine the value of a site, take the average of the
        if square.strength == 0:
            border_value = sum(neighbor.strength
                               for neighbor in self.game_map.neighbors(square) if
                               neighbor.owner not in [0, self.id])

            if border_value == 0:
                # nothing to attack
                border_value = min((self.get_square_metric(neighbor) for neighbor in self.game_map.neighbors(square) if
                                    neighbor.owner == 0), default=0)

        else:
            border_value = self.get_square_metric(square)

        return border_value

    def get_square_metric(self, square: Square):
        return square.production / (square.strength + 1)

    def update_move_targets(self):
        # this will go through spaces and find those that are accessible and then ranked by strength
        border_sites = self.get_unowned_border()

        # create a dict to assoc border sites
        border_assoc = dict()  # type: Dict[Square, List[Square]]

        for border_square in border_sites:
            border_assoc[border_square] = []

        desired_moves = dict()  # type: Dict[Square, Move]

        # update the can attack dict
        can_attack = dict()  # type: Dict[Square, bool]
        for border_square in border_sites:
            can_attack[border_square] = self.can_attack_square(border_square)

        # loop through owned pieces and make the calls to move them
        for location in self.owned_sites:
            # find the closest border spot
            min_location = None
            max_value = 0

            must_attack = False

            if not self.can_move_from(location):
                continue

            for border_square in border_sites:

                if must_attack and not can_attack[border_square]:
                    continue

                distance = self.game_map.get_distance(border_square, location)

                if distance > self.MAX_DISTANCE:
                    continue

                # reset the best spot if this is the first to be attackable
                if distance < self.ATTACK_DIST and can_attack[border_square] and not must_attack:
                    min_location = None
                    max_value = 0
                    must_attack = True

                # threshold the distance to allow for some movement
                if distance <= self.DISTANCE_THRESHOLD:
                    distance = 1

                border_value = self.get_square_value(border_square) / distance

                if border_value > max_value:
                    min_location = border_square
                    max_value = border_value

            # add a check here to see if move should be made

            if min_location is not None:
                border_assoc[min_location].append(location)

        # iterate through the border sites now to determine if to move

        for border_square, locations in border_assoc.items():
            # get the sum of the strengths
            total_strength = 0
            for location in locations:
                total_strength += location.strength

            if total_strength > border_square.strength:
                # if so, move that direction
                for location in locations:
                    move = self.get_next_move(location, border_square)

                    logging.debug("move to make %s", move)

                    if move is not None:
                        desired_moves[location] = move

        # this allows move to be checked a couple times to see if the situation improves
        max_check = 5
        times_checked = 0
        while len(desired_moves) > 0 and times_checked < max_check:
            for key in list(desired_moves.keys()):
                move = desired_moves[key]
                if self.is_move_allowed(move):
                    desired_moves.pop(key)
                    self.moves_this_frame.append(move)
                    # reset move counter if leaving own territory
                    if self.game_map.get_target(move.square, move.direction).owner != self.id:
                        self.time_at_square[move.square] = 0

            times_checked += 1

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
                self.time_at_square[square] += 1
                self.expected_strength[square] = square.strength
                logging.debug("added owned site %s", square)
            else:
                self.time_at_square[square] = 0
                self.expected_strength[square] = -square.strength

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


class Dijkstra:
    graph = defaultdict(list) # type: Dict[Square, List[Square]]

    def __init__(self, game_map: GameMap):
        # iterate through game map
        edges = []  # type: List[Edge]
        for square in game_map:
            # create edge from down and right
            for direction in [EAST, SOUTH]:
                edge = Edge(square, game_map.get_target(square, direction))
                edges.append(edge)

        for edge in edges:
            self.graph[edge.left].append(edge.right)
            self.graph[edge.right].append(edge.left)

    def get_path_for_future(self, start : Square, target : Square, time_total: int):
        seen = set()
        # 'value prod_avail time_to_reach steps'
        max_heap = [(-start.strength, start, (), start.production, 0)]
        side_heap = []

        last_best = None

        while max_heap:
            last_best = heappop(max_heap)
            (future_value, node_current, path, prod_avail, time_now) = last_best

            heappush(side_heap, last_best)

            if node_current not in seen:
                seen.add(node_current)
                new_path = list(path)
                new_path.append(node_current)

                if node_current == target:
                    return (future_value, new_path)

                nodes_to_test = self.graph.get(node_current, ()) # type: List[Square]

                for node_test in nodes_to_test:
                    if node_test not in seen:
                        # determine the time to get there
                        time_addl = node_test.strength // prod_avail

                        new_time_now = time_now + time_addl
                        if new_time_now <= time_total:
                            new_future = future_value - (node_test.production * (2*time_total - new_time_now) - node_test.strength)
                            new_prod_avail = prod_avail + node_test.production
                            heappush(max_heap, (new_future , node_test, new_path, new_prod_avail, new_time_now))
                        else:
                            heappush(side_heap, (new_future, node_test, new_path, new_prod_avail, new_time_now))

        best = heappop(side_heap)
        return (best[0], best[2])
