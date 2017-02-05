import time
from collections import defaultdict
from heapq import *
from typing import Dict
from typing import Set

import numpy as np
from scipy.ndimage.filters import gaussian_filter

from GraphOps import Dijkstra, NodeAvail
from hlt import *

Edge = namedtuple('Edge', 'left right')

Path = namedtuple('Path', 'value prod_avail time_to_reach steps')

start_time = time.time()
TIME_MAX = 0.8


def is_time_out(delta=0.0):
    return time.time() - start_time > TIME_MAX - delta


class HaliteBotCode:
    def __init__(self, game_map: GameMap, id: int, options=defaultdict(None)):
        self.id = id
        self.game_map = game_map
        self.owned_sites = set()  # type: Set[Square]
        self.moves_this_frame = []
        self.expected_strength = dict()  # type: Dict[Square, int]
        self.frame = 0

        self.future_moves = defaultdict(list)  # type: Dict[int, List[Move]]

        self.total_frames = 10 * (self.game_map.height * self.game_map.width) ** 0.5

        self.best_path = []
        self.use_best_path = True

        self.border_sites = None  # type: Set[Square]
        self.attack_squares = set()  # type: Set[Square]

        # will contain the frame where a piece can be checked again
        self.squares_to_skip = dict()  # type: Dict[Square, int]

        self.dij = None  # type: Dijkstra

        self.blurred_values = None

        self.edge_squares = set()
        self.inner_border = set()

        self.DISTANCE_THRESHOLD = 1 if options["DISTANCE_THRESHOLD"] is None else options["DISTANCE_THRESHOLD"]
        self.MAX_DISTANCE = 7 if options["MAX_DISTANCE"] is None else options["MAX_DISTANCE"]
        self.ATTACK_DIST = 3 if options["ATTACK_DIST"] is None else options["ATTACK_DIST"]

        global TIME_MAX
        TIME_MAX = 0.80 if options["TIME_MAX"] is None else options["TIME_MAX"]

    def do_init(self):
        # this will build the distance lookups

        # build the blurred score ratios


        # get an array of floats for production / str + 1 for the game map

        all_data = []
        for y in range(self.game_map.height):
            data = []

            for x in range(self.game_map.width):
                square = self.game_map.get_square(x, y)
                data.append(square.production / (square.strength + 1))

            all_data.append(data)

        a = np.array(all_data)
        self.blurred_values = gaussian_filter(a, sigma=1, mode="wrap")

        return

    def update(self, game_map: GameMap):
        self.game_map = game_map

        global start_time
        start_time = time.time()

        self.moves_this_frame = []

        self.update_owned_sites()
        self.update_border()
        self.update_attack_squares()

        self.dij = Dijkstra(self.game_map, self.id)
        self.update_edge_squares(5, True)

        if not self.use_best_path or len(self.attack_squares):
            logging.debug("attack started, using original scheme")

            self.update_move_targets2()
            self.use_best_path = False
        else:
            logging.debug("no attack, searching best move")
            self.update_best_moves_from_border()
            self.update_moves_with_best_target()

        self.update_moves_for_interior()

        for move in self.future_moves[self.frame]:
            logging.debug("move added: %s", move)
            self.moves_this_frame.append(move)

        self.frame += 1

        logging.debug("total time for update: %f", time.time() - start_time)

        return

    def update_edge_squares(self, dist: int, should_print=False):

        # this updates the squares that are on the edge
        self.edge_squares, self.inner_border = self.dij.get_squares_in_range(self.border_sites, dist)

        # this will print the map to a file to be viewed as a heatmap
        if should_print:
            all_data = []
            for y in range(self.game_map.height):
                data = []
                for x in range(self.game_map.width):
                    value = 0
                    square = self.game_map.get_square(x, y)
                    if square in self.border_sites:
                        value = 1
                    elif square in self.inner_border:
                        value = 2
                    elif square in self.edge_squares:
                        value = 3
                    data.append(value)
                all_data.append(data)
            a = np.array(all_data)
            np.savetxt("logs/maps/%d.txt" % self.frame, a, "%d")

        return

    def update_attack_squares(self):
        self.attack_squares.clear()

        for square in self.border_sites:
            if self.can_attack_from_square(square):
                self.attack_squares.add(square)

        logging.debug("size of attack squares %d", len(self.attack_squares))

        return

    def can_move_from(self, source: Square):
        # must stay at spot to build strength
        allow_move = True

        if source.strength < source.production * 4:
            allow_move = False

        return allow_move

    def is_move_allowed(self, move: Move) -> bool:

        allow_move = True

        source = move.square
        target = self.game_map.get_target(source, move.direction)

        # this should prevent large blocks from combining
        if allow_move:
            if 350 - self.expected_strength[target] < source.strength:
                allow_move = False
            else:
                self.expected_strength[target] += source.strength
                self.expected_strength[source] -= source.strength

        return allow_move

    def can_attack_from_square(self, square: Square) -> bool:
        # this will return a bool indicating if the square can be attacked
        return any(neighbor.owner not in [0, self.id] for neighbor in self.game_map.neighbors(square))

    def get_square_value(self, square: Square) -> float:

        border_value = 1000000

        # this needs to determine the value of a site, take the average of the
        if square.strength == 0:
            border_value = sum(neighbor.strength
                               for neighbor in self.game_map.neighbors(square) if
                               neighbor.owner not in [0, self.id]) * 10

            if border_value == 0:
                # nothing to attack, value pieces near enemy greater... to avoid backing out of battle
                if any(neighbor.owner not in [0, self.id] for neighbor in self.game_map.neighbors(square)):
                    border_value = 2
                else:
                    border_value = 1

        else:
            border_value = self.get_square_metric(square)

        return border_value

    def get_square_metric(self, square: Square):
        # return (square.production * (self.total_frames - self.frame) - square.strength) / 10
        return square.production / (square.strength + 1)

    def update_moves_with_best_target(self):
        # this will iterate through the targets, and find a path to get to them

        # make the graph
        min_length = len(self.best_path) / 2

        skip_del = []
        logging.debug("skip squares contains %s", self.squares_to_skip)
        for square, frame in self.squares_to_skip.items():
            if frame < self.frame:
                skip_del.append(square)
                logging.debug("removing target from skip %s", square)

        for item in skip_del:
            self.squares_to_skip.pop(item)

        # make list of exclusions
        while len(self.best_path) > min_length and not is_time_out(0.1):
            logging.debug("size of best path %d", len(self.best_path))

            value, target = self.best_path[0]
            target = target  # type:Square

            # skip if node has already been tracked
            if target in self.squares_to_skip:
                heappop(self.best_path)
                continue

            exclude = []
            frames_to_del = []
            for frame, moves in self.future_moves.items():
                if frame >= self.frame:
                    for move in moves:
                        exclude.append(move.square)
                else:
                    frames_to_del.append(frame)

            # remove old moves
            for frame in frames_to_del:
                self.future_moves.pop(frame)

            logging.debug("size of excluded squares %d", len(exclude))

            self.dij.update_excludes(exclude)

            logging.debug("going for the target %s with value %f and %f", target, value, time.time() - start_time)

            # get the moves
            value, path = self.dij.get_path_with_strength(target, 5)

            path = path  # type: List[NodeAvail]

            if path is None:
                logging.debug("no path")
            else:
                max_dist = self.set_moves_for_path(path)

                self.squares_to_skip[target] = self.frame + max_dist - 1

                logging.debug("max_dist %d", max_dist)

            heappop(self.best_path)

        return

    def set_moves_for_path(self, path):
        max_dist = 0
        for node in path:
            # get the max distance
            logging.debug("node: %s, prev:%s, dist:%d", node.node, node.previous, node.prev_dist)
            if node.prev_dist > max_dist:
                max_dist = node.prev_dist

        # check for 0 str move at the start... just a wait
        node_del = []
        for node in path:
            if node.prev_dist == max_dist and node.node.strength == 0:
                node_del.append(node)
        for node in node_del:
            path.remove(node)

        # add the moves in the future
        for node in path:
            for direc in [NORTH, SOUTH, EAST, WEST]:
                if self.game_map.get_target(node.node, direc) == node.previous:
                    time_to_move = max_dist - node.prev_dist
                    self.future_moves[self.frame + time_to_move].append(Move(node.node, direc))
                    break
        return max_dist

    def update_best_moves_from_border(self):

        self.best_path = []

        for border_square in self.border_sites:
            border_value = self.blurred_values[border_square.y][border_square.x] + 2 * self.get_square_value(
                border_square)
            heappush(self.best_path, (-border_value, border_square))

        return

    def update_moves_for_interior(self):
        # this will try to push the square in the middle to the edge

        # iterate the edge squares to add to exclude
        # get the border squares

        self.dij.update_excludes((square for square in self.edge_squares if square not in self.inner_border))

        new_excludes = set()

        for frame, list_of_moves in self.future_moves.items():
            for move in list_of_moves:
                new_excludes.add(move.square)

        # iterate the interior border and find a path to the square
        for inner_border_sq in self.inner_border:
            logging.debug("testing inner border %s", inner_border_sq)

            if is_time_out():
                logging.debug("had to interrupt, no time")
                break

            value, path = self.dij.get_path_with_strength(inner_border_sq, 3, 100, 500)

            if path is not None:
                self.set_moves_for_path(path)

                for node_avail in path:
                    new_excludes.add(node_avail.node)

                self.dij.update_excludes(new_excludes)

        return

    def update_move_targets2(self):
        # this will go through spaces and find those that are accessible and then ranked by strength

        # create a dict to assoc border sites
        border_assoc = defaultdict(list)  # type: Dict[Square, List[Square]]

        desired_moves = dict()  # type: Dict[Square, Move]

        border_to_test = sorted(self.border_sites, key=self.get_square_value, reverse=True)

        logging.debug("size of the border before %d", len(border_to_test))

        border_to_test = border_to_test[:len(border_to_test) // 2]

        logging.debug("size of the border after %d", len(border_to_test))

        # loop through owned pieces and make the calls to move them
        for location in self.owned_sites:
            if is_time_out(0.1):
                break

            # skip those squares not in the edge
            if location not in self.edge_squares:
                continue

            if location.strength == 0:
                continue

            # find the closest border spot
            min_location = None
            max_value = 0
            min_distance = 1000

            if not self.can_move_from(location):
                continue

            for border_square in border_to_test:
                if is_time_out(0.1):
                    break

                distance = self.game_map.get_distance(border_square, location)

                # threshold the distance to allow for some movement
                if distance <= self.DISTANCE_THRESHOLD:
                    distance = 1

                border_value = self.get_square_value(border_square)

                if distance < min_distance or (distance == min_distance and border_value > max_value):
                    min_location = border_square
                    max_value = border_value
                    min_distance = distance

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

                    if move is not None:
                        desired_moves[location] = move

        # this allows move to be checked a couple times to see if the situation improves
        max_check = 5
        times_checked = 0

        if not is_time_out():
            self.moves_this_frame.clear()

        while len(desired_moves) > 0 and times_checked < max_check:
            if is_time_out():
                break
            for key in list(desired_moves.keys()):
                move = desired_moves[key]
                if self.is_move_allowed(move):
                    desired_moves.pop(key)
                    self.moves_this_frame.append(move)

            times_checked += 1

        return

    def get_next_move(self, start: Square, target: Square) -> Move:

        steps, path = self.dij.get_path(start, target)

        if path is not None:
            direction = self.game_map.get_direction(path[0], path[1])
            return Move(start, direction)

        return None

    def update_owned_sites(self):

        self.owned_sites = list()

        # this will update the list of sites that are owned by self (will contain locations)
        for square in self.game_map:
            if square.owner == self.id:
                self.owned_sites.append(square)
                self.expected_strength[square] = square.strength
            else:
                self.expected_strength[square] = -square.strength

        return

    def update_border(self):
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
        self.border_sites = border_sites

        return
