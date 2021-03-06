import time
from collections import defaultdict
from heapq import *
from typing import Dict
from typing import Set
from typing import Tuple

import numpy as np
from scipy.ndimage.filters import gaussian_filter

from GraphOps import Dijkstra, NodeAvail
from hlt import *

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
        self.update_edge_squares(self.MAX_DISTANCE, False)

        logging.debug("skip squares contains %s", self.squares_to_skip)
        self.update_skip_squares()  # make list of exclusions

        # use the old scheme if able to attack
        if not self.use_best_path or any(self.can_attack_from_square(square) for square in self.border_sites):
            logging.debug("attack started, using original scheme")

            self.update_complex_moves()
            self.use_best_path = False
        else:
            logging.debug("no attack, searching best move")
            self.update_best_moves_from_border()
            self.update_moves_with_best_target()

        for move in self.future_moves[self.frame]:
            logging.debug("move added: %s", move)
            self.moves_this_frame.append(move)

        self.frame += 1

        logging.debug("total time for update: %f", time.time() - start_time)

        return

    def update_edge_squares(self, dist: int, should_print=False):

        # this updates the squares that are on the edge
        self.edge_squares, self.inner_border = self.dij.get_squares_in_range(self.attack_squares, dist)

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

    def has_zero_str_neighbors(self, square):
        for neighbor in self.game_map.neighbors(square):
            if neighbor.strength == 0 or neighbor.owner == self.id:
                return True

        return False

    def update_attack_squares(self):
        self.attack_squares.clear()

        for square in self.border_sites:
            if self.can_attack_from_square(square) or self.has_zero_str_neighbors(square):
                self.attack_squares.add(square)

        logging.debug("size of attack squares %d", len(self.attack_squares))

        return

    def can_move_from(self, source: Square):
        # must stay at spot to build strength
        allow_move = True

        if source.strength < min(source.production * 4, 50):
            allow_move = False

        return allow_move

    def can_attack_from_square(self, square: Square) -> bool:
        # this will return a bool indicating if the square can be attacked
        return any(neighbor.owner not in [0, self.id] and neighbor.strength == 0 for neighbor in self.game_map.neighbors(square))

    def get_square_value(self, square: Square) -> float:

        # this needs to determine the value of a site, take the average of the
        if square.strength == 0:
            border_value = sum(neighbor.strength
                               for neighbor in self.game_map.neighbors(square) if
                               neighbor.owner not in [0, self.id]) * 10

            # this will return the total of the enemy str or 1000 for a valuable 0 str spot.
            return border_value if border_value > 0 else 1000

        return self.get_square_metric(square)

    def get_square_metric(self, square: Square):
        # return (square.production * (self.total_frames - self.frame) - square.strength) / 10
        return square.production / (square.strength + 1)

    def update_moves_with_best_target(self):
        # this will iterate through the targets, and find a path to get to them

        # make the graph
        min_length = len(self.best_path) / 2

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

    def update_skip_squares(self):
        skip_del = []
        for square, frame in self.squares_to_skip.items():
            if frame < self.frame:
                skip_del.append(square)
                logging.debug("removing target from skip %s", square)
        for item in skip_del:
            self.squares_to_skip.pop(item)

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
            border_value = self.blurred_values[border_square.y][border_square.x] + self.get_square_value(
                border_square)
            heappush(self.best_path, (-border_value, border_square))

        return

    def get_enemy_strength_from_square(self, start: List[Square], dist: int) -> Set[Square]:
        seen = set()
        max_heap = []
        heappush(max_heap, (0, start))
        enemy_strength = 0

        is_start = True

        while max_heap:
            last_best = heappop(max_heap)
            (current_distance, node_current) = last_best
            node_current = node_current  # type: Square
            if node_current not in seen:
                seen.add(node_current)
                if current_distance > dist or (node_current.owner == self.id and not is_start):
                    is_start = False
                    continue

                is_start = False

                if node_current.owner == 0 and node_current.strength > 0:
                    continue

                if node_current.owner not in [0, self.id]:
                    enemy_strength += node_current.strength

                for node_test in self.game_map.neighbors(node_current):
                    # check the nodes not currently on the path
                    if node_test not in seen:
                        if (node_test.owner == 0 and node_test.strength == 0) or node_test.owner != self.id:
                            new_future = current_distance + 1
                            heappush(max_heap, (new_future, node_test))

        return enemy_strength

    def update_complex_moves(self):
        # this will go through spaces and find those that are accessible and then ranked by strength

        # create a dict to assoc border sites

        owned_at_border, other = self.dij.get_squares_in_range(self.border_sites, 1)

        current_values = dict()  # type: Dict[Square, Tuple[int, Square, Square]]

        enemy_waiting = []

        squares_processed = set()

        expected_strength = dict() # type: Dict[Square, int]
        for square in self.owned_sites:
            expected_strength[square] = square.strength

        for square in owned_at_border:
            if is_time_out():
                logging.debug("ran out of time in finding squares to target")
                break
            # get the strength and skip move if 0
            str_from_spot = self.get_enemy_strength_from_square(square, 5)
            if str_from_spot == 0:
                continue

            new_entry = (-str_from_spot, square, None)
            current_values[square] = new_entry
            heappush(enemy_waiting, new_entry)
            logging.debug("square %s sees enemy str %d", square, new_entry[0])

        # handle the case where there are no attacks after entering CAS mode
        if not enemy_waiting:
            logging.debug("no attack avail, processing border value")
            for square in owned_at_border:
                if is_time_out():
                    logging.debug("ran out of time in finding squares to target")
                    break

            value = self.get_square_value(square)

            new_entry = (-value, square, None)
            current_values[square] = new_entry
            heappush(enemy_waiting, new_entry)
            logging.debug("square %s sees enemy str %d", square, new_entry[0])

        while enemy_waiting:
            if is_time_out():
                logging.debug("ran out of time in enemy_waiting loop")
                break

            str_need, square, prev_square = heappop(enemy_waiting)

            logging.debug("processing square %s from %s w/ str %f", square, prev_square, str_need)

            if square in squares_processed:
                continue

            if self.can_move_from(square):
                if prev_square is None:
                    # these are the first moves, decide where to go, check neighbors make move
                    # get the value of the neighbors and move there
                    max_value = 0
                    best_target = None
                    for possible_target in self.game_map.neighbors(square):
                        if possible_target.owner != self.id and self.is_move_ok_with_str(square, possible_target):
                            value = self.get_square_value(possible_target)
                            if value > max_value:
                                best_target = possible_target
                                max_value = value

                    if best_target is not None:
                        logging.debug("square is going after %s %s %f", square, best_target, max_value)
                        # have a good target, add the move
                        self.add_move_if_str_ok(square, best_target)

                else:
                    # these need to follow the leader if they have strength
                    logging.debug("square %s is following prev %s", square, prev_square)

                    # check if there is a 0 -str neighbor to grab
                    neighbors = self.game_map.neighbors(square)

                    move = None

                    for neighbor in neighbors:
                        # this will take a square if its a 0 str sitting off the main attack
                        takeNeighbor1 = neighbor.owner != self.id and neighbor.strength == 0 and self.expected_strength[
                                                                                                 neighbor] == 0
                        # this will attack a square if we already have 3 sides of it
                        takeNeighbor2 = neighbor.owner == 0 and sum(1 for neigh in self.game_map.neighbors(neighbor) if neigh.owner == self.id) > 2 and square.strength > neighbor.strength
                        if takeNeighbor1 or takeNeighbor2:
                            move = self.add_move_if_str_ok(square, neighbor)
                            if move is not None:
                                logging.debug("taking a 0 str spot %s to %s", square, neighbor)
                                break

                    # check the expected strength
                    if move is None:
                        move = self.add_move_if_str_ok(square, prev_square)
                        if move is None:
                            # search for a new move if prev square is taken
                            for neighbor in neighbors:
                                if neighbor.owner == self.id:
                                    move = self.add_move_if_str_ok(square, neighbor)
                                    if move is not None:
                                        break

            squares_processed.add(square)

            neighbor_count = 0

            for next_square in self.game_map.neighbors(square):
                if next_square.owner == self.id:
                    neighbor_count += 1

            if neighbor_count > 0:
                str_need = str_need / neighbor_count
                logging.debug("str_need: %f", str_need)

            # take that strength and add to the neighbors as they are processed
            for next_square in self.game_map.neighbors(square):
                if next_square in squares_processed:
                    continue

                # only make moves for the neighbors that we own
                if next_square.owner == self.id:
                    if next_square in current_values:
                        # this will update the current entry and reheap the heap
                        prev_str, sq1, sq2 = current_values[next_square]
                        current_values[next_square] = (prev_str + str_need, sq1, sq2)
                        logging.debug("update sq str need to %s %f", next_square, current_values[next_square][0])
                        heappush(enemy_waiting, current_values[next_square])
                    else:
                        # this will add a new entry to the heap
                        new_entry = (str_need, next_square, square)
                        current_values[next_square] = new_entry
                        heappush(enemy_waiting, new_entry)
                        logging.debug("added new entry for neighbor %s %s", next_square, new_entry)

        logging.debug("done with processing borders")
        return

    def is_move_ok_with_str(self, start:Square, target:Square):
        logging.debug("str expect and str avail %d %d", self.expected_strength[target], start.strength)
        return (self.expected_strength[target] + start.strength) < 300

    def add_move_if_str_ok(self, start: Square, target: Square):
        if self.is_move_ok_with_str(start, target):
            move = self.game_map.get_move(start, target)
            logging.debug("move for %s was found %s", start, move)
            if move is not None:
                self.expected_strength[start] -= start.strength
                self.expected_strength[target] += start.strength
                self.moves_this_frame.append(move)

                logging.debug("move was added %s target %s", move, self.game_map.get_target(start, move.direction))

                return Move

        return None

    def add_future_moves(self, start: Square, target: Square) -> Move:

        steps, path = self.dij.get_path(start, target)

        if path is not None:
            frames_ahead = 0
            while frames_ahead < len(path) - 1:

                source = path[0 + frames_ahead]
                dest = path[1 + frames_ahead]

                if dest in self.squares_to_skip or source in self.squares_to_skip:
                    break

                if dest in self.edge_squares:
                    break

                direction = self.game_map.get_direction(source, dest)
                logging.debug("adding future move from %s to %s in %d", source, dest, frames_ahead)
                self.future_moves[self.frame + frames_ahead].append(Move(start, direction))
                self.squares_to_skip[dest] = self.frame + frames_ahead + 2

                frames_ahead += 1

        return None

    def get_next_move(self, start: Square, target: Square) -> Move:

        steps, path = self.dij.get_path(start, target)

        if path is not None and len(path) > 1:
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

        logging.debug("size of owned sites %d", len(self.owned_sites))

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
