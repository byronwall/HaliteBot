import random
from typing import Dict
from typing import List
from typing import Set

import time

from hlt import *
import logging

from collections import defaultdict
from heapq import *

Edge = namedtuple('Edge', 'left right')

Path = namedtuple('Path', 'value prod_avail time_to_reach steps')

NodeAvail = namedtuple("NodeAvail", "node previous prev_dist")


class HaliteBotCode:
    def __init__(self, game_map: GameMap, id: int, options=defaultdict(None)):
        self.id = id
        self.game_map = game_map
        self.owned_sites = set()  # type: Set[Square]
        self.moves_this_frame = []
        self.expected_strength = dict()  # type: Dict[Square, int]
        self.frame = 0

        self.future_moves = defaultdict(list)

        self.total_frames = 10 * (self.game_map.height * self.game_map.width) ** 0.5

        self.best_path = []
        self.start_time = time.time()
        self.use_best_path = True

        self.dij = None  # type: Dijkstra

        self.DISTANCE_THRESHOLD = 1 if options["DISTANCE_THRESHOLD"] is None else options["DISTANCE_THRESHOLD"]
        self.MAX_DISTANCE = 5 if options["MAX_DISTANCE"] is None else options["MAX_DISTANCE"]
        self.ATTACK_DIST = 3 if options["ATTACK_DIST"] is None else options["ATTACK_DIST"]
        self.TIME_MAX = 0.85 if options["TIME_MAX"] is None else options["TIME_MAX"]

    def update(self, game_map: GameMap):
        self.game_map = game_map

        self.start_time = time.time()

        self.moves_this_frame = []
        self.update_owned_sites()

        border_squares = self.get_unowned_border()

        if not self.use_best_path or any(self.can_attack_from_square(square) for square in border_squares):
            logging.debug("attack started, using original scheme")
            self.future_moves.clear()

            self.dij = Dijkstra(self.game_map, self.id)

            self.update_move_targets2()
            self.use_best_path = False
        else:
            logging.debug("no attack, searching best move")
            self.update_best_moves_from_border()
            self.update_moves_with_best_target()

        self.frame += 1

        return

    def can_move_from(self, source: Square):
        # must stay at spot to build strength
        allow_move = True

        if source.strength < source.production * 10:
            allow_move = False

        return allow_move

    def is_move_allowed(self, move: Move) -> bool:

        allow_move = True

        source = move.square
        target = self.game_map.get_target(source, move.direction)

        # this should prevent large blocks from combining
        if allow_move:
            if 280 - self.expected_strength[target] < source.strength:
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
                               neighbor.owner not in [0, self.id])

            if border_value == 0:
                # nothing to attack
                border_value = 1000

        else:
            border_value = self.get_square_metric(square)

        return border_value

    def get_square_metric(self, square: Square):
        return square.production  / (square.strength + 1)
        return (square.production * (self.total_frames - self.frame) - square.strength) / 100

    def is_time_close(self) -> bool:
        return time.time() - self.start_time > self.TIME_MAX

    def update_moves_with_best_target(self):
        # this will iterate through the targets, and find a path to get to them

        # make the graph
        min_length = len(self.best_path) / 2

        # make list of exclusions
        while len(self.best_path) > min_length and not self.is_time_close():
            logging.debug("size of best path %d", len(self.best_path))
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

            dij = Dijkstra(self.game_map, self.id, exclude)

            value, target = self.best_path[0]  # type:Square
            target = self.game_map.get_square(target.x, target.y)

            logging.debug("going for the target %s with value %f", target, value)

            # get the moves
            value, path = dij.get_path_with_strength(target, 5)

            path = path  # type: List[NodeAvail]

            if path is None:
                logging.debug("no path")
            else:
                max_dist = 0
                for node in path:
                    # get the max distance
                    logging.debug("node: %s, prev:%s, dist:%d", node.node, node.previous, node.prev_dist)
                    if node.prev_dist > max_dist:
                        max_dist = node.prev_dist

                # add the moves in the future
                for node in path:
                    for direc in [NORTH, SOUTH, EAST, WEST]:
                        if self.game_map.get_target(node.node, direc) == node.previous:
                            time_to_move = max_dist - node.prev_dist
                            self.future_moves[self.frame + time_to_move].append(Move(node.node, direc))
                            break

                logging.debug("max_dist %d", max_dist)

            heappop(self.best_path)

        # add the moves in

        self.moves_this_frame = self.future_moves[self.frame]

        return

    def update_best_moves_from_border(self):

        border_sites = self.get_unowned_border()

        self.best_path = []

        for border_square in border_sites:
            border_value = self.get_square_value(border_square)
            heappush(self.best_path, (-border_value, border_square))

        return

    def update_move_targets2(self):
        # this will go through spaces and find those that are accessible and then ranked by strength
        border_sites = self.get_unowned_border()

        # create a dict to assoc border sites
        border_assoc = defaultdict(list)  # type: Dict[Square, List[Square]]

        desired_moves = dict()  # type: Dict[Square, Move]

        # update the can attack dict
        can_attack = dict()  # type: Dict[Square, bool]
        for border_square in border_sites:
            can_attack[border_square] = self.can_attack_from_square(border_square)

        # loop through owned pieces and make the calls to move them
        for location in self.owned_sites:
            if self.is_time_close():
                break

            # find the closest border spot
            min_location = None
            max_value = 0
            min_distance = 1000

            should_move = location.strength > min(location.production * 40, 240)

            if not self.can_move_from(location):
                continue

            for border_square in border_sites:

                distance = self.game_map.get_distance(border_square, location)

                if distance > self.MAX_DISTANCE and not should_move:
                    continue

                # threshold the distance to allow for some movement
                if distance <= self.DISTANCE_THRESHOLD:
                    distance = 1

                border_value = self.get_square_value(border_square)

                if distance<min_distance or(distance == min_distance and border_value > max_value):
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

            if total_strength > border_square.strength or self.can_attack_from_square(border_square):
                # if so, move that direction
                for location in locations:
                    move = self.get_next_move(location, border_square)

                    if move is not None:
                        desired_moves[location] = move

        # this allows move to be checked a couple times to see if the situation improves
        max_check = 3
        times_checked = 0
        while len(desired_moves) > 0 and times_checked < max_check:
            if self.is_time_close():
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
            logging.debug("graph direction %d", direction)
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
    squares = []  # type: List[Square]

    def __init__(self, game_map: GameMap, owner_required=0, exclude=[]):
        # iterate through game map
        self.game_map = game_map  # type: GameMap
        self.id = owner_required
        self.graph = defaultdict(list)  # type: Dict[Square, List[Square]]

        edges = []  # type: List[Edge]
        for square in game_map:
            # create edge from down and right
            if owner_required > 0 and square.owner != owner_required:
                # only want squares with a certain owner
                continue

            if square in exclude:
                continue

            for direction in [EAST, WEST, NORTH, SOUTH]:
                edge = Edge(square, game_map.get_target(square, direction))
                edges.append(edge)

        for edge in edges:
            if edge.right not in exclude:
                self.graph[edge.left].append(edge.right)

            if edge.left not in exclude:
                self.graph[edge.right].append(edge.left)

    def get_path_with_strength(self, start: Square, size_max: int, strength_goal=0):

        if strength_goal == 0:
            strength_goal = 10 if start.strength == 0 else start.strength

        # 'value prod_avail time_to_reach steps'
        max_heap = [(0, NodeAvail(start, None, 0), [], set(), [])]
        side_heap = []

        shortest_in_side_heap = size_max + 1

        while max_heap:
            last_best = heappop(max_heap)
            (strength_total, node_current, path, nodes_avail, path_infos) = last_best
            node_current = node_current  # type: NodeAvail
            if node_current.node not in path:
                # copy the set to prevent cross talk
                nodes_avail = set(nodes_avail)  # type: Set[NodeAvail]
                if len(nodes_avail):
                    nodes_avail.remove(node_current)

                new_path = list(path)  # type: List[Square]
                new_path.append(node_current.node)

                if -strength_total > strength_goal:
                    if len(new_path) < shortest_in_side_heap:
                        shortest_in_side_heap = len(new_path)

                    heappush(side_heap, (len(new_path), path_infos))
                    continue

                # throw out this route if longer than current shortest route
                if len(new_path) > shortest_in_side_heap:
                    continue

                nodes_to_test = self.graph.get(node_current.node, ())  # type: List[Square]

                for node in nodes_to_test:
                    # only test those nodes we own
                    if node.owner == self.id:
                        nodes_avail.add(NodeAvail(node, node_current.node, node_current.prev_dist + 1))

                for node_test in nodes_avail:
                    # check the nodes not currently on the path
                    if node_test.node not in new_path:
                        # determine the time to get there
                        if len(new_path) <= size_max:
                            new_infos = list(path_infos)
                            new_infos.append(node_test)

                            heappush(max_heap, (
                                (strength_total - node_test.node.strength), node_test, new_path, nodes_avail,
                                new_infos))

        if side_heap:
            best = heappop(side_heap)
        else:
            best = (0, None)

        return best

    def get_path(self, start: Square, target: Square):
        seen = set()
        max_heap = [(0, start, ())]

        while max_heap:
            last_best = heappop(max_heap)
            (future_value, node_current, path) = last_best

            if node_current not in seen:

                seen.add(node_current)

                new_path = list(path)
                new_path.append(node_current)

                if node_current == target:
                    return (future_value, new_path)

                nodes_to_test = self.graph.get(node_current, ())  # type: List[Square]

                for node_test in nodes_to_test:
                    # check the nodes not currently on the path
                    if node_test not in seen:
                        # determine the time to get there
                        new_future = future_value + 1

                        heappush(max_heap, (new_future, node_test, new_path))

        return (None, None)
