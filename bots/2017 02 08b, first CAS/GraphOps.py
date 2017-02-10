import logging
from collections import defaultdict, namedtuple
from heapq import heappop, heappush
from typing import List, Set

from hlt import GameMap, Square

NodeAvail = namedtuple("NodeAvail", "node previous prev_dist")


class Dijkstra:
    squares = []  # type: List[Square]

    def __init__(self, game_map: GameMap, owner_required=0, exclude=[]):
        # iterate through game map
        self.game_map = game_map  # type: GameMap
        self.id = owner_required
        self.graph = defaultdict(list)  # type: Dict[Square, List[Square]]

        for square in game_map:
            # create edge from down and right
            if owner_required > 0 and square.owner != owner_required:
                # only want squares with a certain owner
                continue

            if square in exclude:
                continue

            for target in game_map.neighbors(square):
                self.graph[square].append(target)
                self.graph[target].append(square)

        self.update_excludes(exclude)

    def add_square_and_neighbors(self, square: Square):
        for target in self.game_map.neighbors(square):
            self.graph[square].append(target)
            self.graph[target].append(square)

        return

    def update_excludes(self, exclude=[]):

        for del_sq in exclude:
            if del_sq in self.graph:
                self.graph.pop(del_sq)

        return

    def get_path_with_strength(self, start: Square, size_max: int, strength_goal=0, str_max=255):

        if start not in self.graph:
            (0, None)

        if strength_goal == 0:
            strength_goal = 10 if start.strength == 0 else start.strength

        # 'value prod_avail time_to_reach steps'
        max_heap = [(0, NodeAvail(start, None, 0), [], set(), [], 0, 1)]
        side_heap = []

        shortest_in_side_heap = size_max + 1


        paths_tested = set()  # type: Set[Set[Square]

        counter = 0
        while max_heap:
            counter += 1
            if counter % 10 == 0:
                # this seems to be required becuase of cyclic imports
                from HaliteBotCode import is_time_out
                if is_time_out(0.1):
                    break
            last_best = heappop(max_heap)  # type: Tuple[int, NodeAvail, Set[NodeAvail], List[NodeAvail], int, int]
            (strength_total, node_current, path, nodes_avail, path_infos, prod_avail, max_dist) = last_best

            if node_current.node not in path:
                # copy the set to prevent cross talk
                nodes_avail = set(nodes_avail)  # type: Set[NodeAvail]
                if len(nodes_avail):
                    nodes_avail.remove(node_current)

                new_path = list(path)  # type: List[Square]
                new_path.append(node_current.node)

                # build the FrozenSet to add to tested paths
                path_set = frozenset(new_path)
                if path_set in paths_tested:
                    continue

                paths_tested.add(path_set)

                # check if this increases the max distance, if so add the production in
                if node_current.prev_dist > max_dist:
                    max_dist = node_current.prev_dist
                    strength_total -= prod_avail

                # add the new prod after checking if this extends the max
                if len(new_path) > 1:
                    prod_avail += node_current.node.production

                if strength_goal < -strength_total <= str_max:
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
                    # testing to see if it is in the graph ensures that it shoudl be accessible
                    if node in self.graph and node.owner == self.id:
                        nodes_avail.add(NodeAvail(node, node_current.node, node_current.prev_dist + 1))

                for node_test in nodes_avail:
                    # check the nodes not currently on the path
                    if node_test.node not in new_path:
                        if len(new_path) <= size_max:
                            new_infos = list(path_infos)
                            new_infos.append(node_test)

                            heappush(max_heap, (
                                (strength_total - node_test.node.strength), node_test, new_path, nodes_avail, new_infos,
                                prod_avail, max_dist))

        if side_heap:
            best = heappop(side_heap)
        else:
            best = (0, None)

        logging.debug("best path was %s", best)
        logging.debug("processing path took %d iterations", counter)

        return best

    def get_path(self, start: Square, target: Square):
        if target is None:
            return (None, None)

        seen = set()
        max_heap = [(0, start, ())]

        counter = 0
        while max_heap:
            counter += 1
            if counter % 10 == 0:
                # this seems to be required becuase of cyclic imports
                from HaliteBotCode import is_time_out
                if is_time_out(0.1):
                    break
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
                    if node_test not in seen and node_test in self.graph:
                        # determine the time to get there
                        # try a little A* here
                        new_future = future_value + 1 + self.game_map.get_distance(node_test, target)

                        heappush(max_heap, (new_future, node_test, new_path))

        return (None, None)

    def get_squares_in_range(self, start: List[Square], dist: int) -> Set[Square]:
        seen = set()

        max_heap = []
        for square in start:
            heappush(max_heap, (0, square))

        final_range = set()
        inner_border = set()

        while max_heap:
            last_best = heappop(max_heap)
            (current_distance, node_current) = last_best

            if node_current not in seen:
                seen.add(node_current)

                if current_distance > dist:
                    continue

                if current_distance == dist:
                    inner_border.add(node_current)

                if node_current.owner == self.id:
                    final_range.add(node_current)

                nodes_to_test = self.graph.get(node_current, ())  # type: List[Square]

                for node_test in nodes_to_test:
                    # check the nodes not currently on the path
                    if node_test not in seen and node_test in self.graph and node_test not in final_range:
                        # determine the time to get there
                        # try a little A* here
                        new_future = current_distance + 1

                        heappush(max_heap, (new_future, node_test))

        return (final_range, inner_border)
