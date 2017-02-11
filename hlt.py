import sys
from collections import defaultdict
from collections import namedtuple
from itertools import chain, zip_longest
from typing import Dict
from typing import List, Iterable

import logging
from typing import Set


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


NORTH, EAST, SOUTH, WEST, STILL = range(5)


def opposite_cardinal(direction):
    "Returns the opposing cardinal direction."
    return (direction + 2) % 4 if direction != STILL else STILL


_square = namedtuple('Square', 'x y owner strength production id')

dict_distance = defaultdict(lambda: defaultdict(lambda: -1)) # type: Dict[Square, Dict[Square, int]]


class Square(_square):
    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return "(%d,%d #%d p%d id%d)" % (self.x, self.y, self.strength, self.production, self.id)


Move = namedtuple('Move', 'square direction')


class GameMap:
    def __init__(self, size_string, production_string, map_string=None):
        logging.debug("size_string:" + size_string)
        logging.debug("production_string:" + production_string)

        self.width, self.height = tuple(map(int, size_string.split()))
        self.production = tuple(
            tuple(map(int, substring)) for substring in grouper(production_string.split(), self.width))
        self.contents = None
        self.get_frame(map_string)
        self.starting_player_count = len(set(square.owner for square in self)) - 1

    def get_frame(self, map_string=None):
        "Updates the map information from the latest frame provided by the Halite game environment."
        if map_string is None:
            map_string = get_string()

        logging.debug("map_string:" + map_string)
        split_string = map_string.split()
        owners = list()
        while len(owners) < self.width * self.height:
            counter = int(split_string.pop(0))
            owner = int(split_string.pop(0))
            owners.extend([owner] * counter)
        assert len(owners) == self.width * self.height
        assert len(split_string) == self.width * self.height
        self.contents = [[Square(x, y, owner, strength, production, x * self.width + y)
                          for x, (owner, strength, production)
                          in enumerate(zip(owner_row, strength_row, production_row))]
                         for y, (owner_row, strength_row, production_row)
                         in enumerate(zip(grouper(owners, self.width),
                                          grouper(map(int, split_string), self.width),
                                          self.production))]

    def __iter__(self) -> Iterable[Square]:
        "Allows direct iteration over all squares in the GameMap instance."
        return chain.from_iterable(self.contents)

    def neighbors(self, square: Square, n: int = 1, include_self: bool = False) -> Iterable[Square]:
        "Iterable over the n-distance neighbors of a given square.  For single-step neighbors, the enumeration index provides the direction associated with the neighbor."
        assert isinstance(include_self, bool)
        assert isinstance(n, int) and n > 0
        if n == 1:
            combos = ((0, -1), (1, 0), (0, 1), (-1, 0), (0,
                                                         0))  # NORTH, EAST, SOUTH, WEST, STILL ... matches indices provided by enumerate(game_map.neighbors(square))
        else:
            combos = ((dx, dy) for dy in range(-n, n + 1) for dx in range(-n, n + 1) if abs(dx) + abs(dy) <= n)
        return (self.contents[(square.y + dy) % self.height][(square.x + dx) % self.width] for dx, dy in combos if
                include_self or dx or dy)

    def get_target(self, square, direction=STILL) -> Square:
        "Returns a single, one-step neighbor in a given direction."
        dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))[direction]
        return self.contents[(square.y + dy) % self.height][(square.x + dx) % self.width]

    def get_distance(self, sq1: Square, sq2: Square):
        "Returns Manhattan distance between two squares."

        if sq1.x < sq2.x or (sq1.x == sq2.x and sq1.y < sq2.y):
            first = sq1.id
            second = sq2.id
        else:
            first = sq2.id
            second = sq1.id

        dist = dict_distance[first][second]

        if dist > -1:
            return dist

        dist = min(abs(sq1.x - sq2.x), self.width - abs(sq2.x - sq1.x)) + min(abs(sq1.y - sq2.y),
                                                                                  self.height - abs(sq2.y - sq1.y))

        dict_distance[first][second] = dist

        return dist

    def get_square(self, x: int, y: int) -> Square:
        return self.contents[y][x]

    def get_direction(self, start: Square, neighbor: Square):
        for direc in [NORTH, SOUTH, EAST, WEST]:
            if self.get_target(start, direc) == neighbor:
                return direc
                break

        return -1

    def get_move(self, start: Square, target: Square):
        if self.get_distance(start, target) == 1:
            return Move(start, self.get_direction(start, target))

        return None

#################################################################
# Functions for communicating with the Halite game environment  #
#################################################################


def send_string(s):
    sys.stdout.write(s)
    sys.stdout.write('\n')
    sys.stdout.flush()


def get_string():
    next_line = sys.stdin.readline().rstrip('\n')
    return next_line


def get_init():
    playerID = int(get_string())
    m = GameMap(get_string(), get_string())
    return playerID, m


def send_init(name):
    send_string(name)


def translate_cardinal(direction):
    "Translate direction constants used by this Python-based bot framework to that used by the official Halite game environment."
    return (direction + 1) % 5


def send_frame(moves):
    send_string(' '.join(
        str(move.square.x) + ' ' + str(move.square.y) + ' ' + str(translate_cardinal(move.direction)) for move in
        moves))
