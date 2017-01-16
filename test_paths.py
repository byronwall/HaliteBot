import os
import hlt
import logging
import time
import cProfile
import argparse
from HaliteBotCode import *

size_string = "10 10"
prod_string = "2 2 3 7 5 3 3 2 2 2 3 3 3 4 4 6 7 4 3 2 3 2 2 4 5 6 6 5 3 2 2 2 2 3 4 4 4 4 2 2 2 2 1 1 2 4 7 4 2 2 2 2 2 3 3 5 7 3 2 2 2 3 4 7 6 4 4 3 3 3 2 3 5 6 6 5 4 2 2 3 2 2 4 4 4 4 3 2 2 2 2 2 4 7 4 2 1 1 2 2"
map_string = "7 0 1 2 44 0 1 1 47 0 127 127 80 35 42 52 71 101 88 92 148 184 97 46 35 46 60 61 67 89 122 171 101 81 71 88 64 59 54 81 99 136 118 91 86 147 97 81 79 107 77 90 116 84 63 92 71 112 114 118 92 88 101 71 52 42 35 80 127 127 89 67 61 60 46 35 46 97 184 148 81 54 59 64 88 71 81 101 171 122 107 79 81 97 147 86 91 118 136 99 118 114 112 71 92 63 84 116 90 77"

size_string = "20 20"
prod_string = "0 0 0 1 0 0 0 1 2 2 1 1 1 1 1 1 0 1 1 1 1 0 0 1 0 0 1 2 2 2 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 2 2 2 1 1 2 2 2 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 2 1 1 2 1 1 1 1 1 1 1 0 0 1 1 1 2 3 3 3 2 1 1 1 1 1 1 1 1 1 1 0 1 1 1 2 2 3 3 3 1 1 1 1 1 1 1 2 2 2 1 1 1 1 2 2 2 3 3 2 1 0 1 1 1 2 2 2 2 2 1 1 1 1 2 2 3 3 4 3 1 0 0 1 1 2 2 3 2 1 1 1 1 1 2 3 3 4 6 4 1 0 0 1 1 1 2 3 2 1 1 0 1 1 1 2 2 4 6 4 1 0 0 1 1 1 2 3 2 1 1 0 1 1 1 2 2 4 6 4 1 0 0 1 1 2 2 3 2 1 1 1 1 1 2 3 3 4 6 4 1 0 1 1 1 2 2 2 2 2 1 1 1 1 2 2 3 3 4 3 1 1 1 1 1 1 1 2 2 2 1 1 1 1 2 2 2 3 3 2 2 1 1 1 1 1 1 1 1 1 1 0 1 1 1 2 2 3 3 3 2 1 1 2 1 1 1 1 1 1 1 0 0 1 1 1 2 3 3 3 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 1 1 1 1 1 0 1 2 2 2 1 1 2 2 2 1 1 1 1 1 1 0 0 1 0 0 1 2 2 2 1 1 1 1 1 1 1 1 1 1 0 0 0 1 0 0 0 1 2 2 1 1 1 1 1 1 0 1 1 1"
map_string = "110 0 1 1 179 0 1 2 109 0 47 77 148 118 85 99 95 125 130 84 51 71 125 127 109 73 69 115 129 76 49 84 146 122 87 95 113 180 196 127 69 63 89 91 92 64 68 120 120 73 60 87 122 103 79 84 118 208 218 157 89 66 72 65 64 46 54 101 103 78 51 59 79 70 62 61 97 185 189 154 77 46 55 61 63 47 51 91 92 74 45 34 48 59 62 52 84 162 170 131 54 27 39 56 70 50 48 84 92 76 39 23 34 54 59 40 56 112 128 94 39 25 37 50 59 44 52 88 104 78 34 15 21 39 49 42 58 89 89 73 45 40 51 57 52 50 68 96 114 82 26 13 21 34 44 51 77 97 88 92 73 60 61 67 58 57 74 99 113 71 17 17 29 42 44 52 77 108 116 123 82 65 78 98 80 63 68 72 70 39 14 16 28 40 41 51 69 120 155 161 94 78 98 118 91 52 46 54 52 28 14 16 28 40 41 51 69 120 155 161 94 78 98 118 91 52 46 54 52 28 17 17 29 42 44 52 77 108 116 123 82 65 78 98 80 63 68 72 70 39 26 13 21 34 44 51 77 97 88 92 73 60 61 67 58 57 74 99 113 71 34 15 21 39 49 42 58 89 89 73 45 40 51 57 52 50 68 96 114 82 39 23 34 54 59 40 56 112 128 94 39 25 37 50 59 44 52 88 104 78 45 34 48 59 62 52 84 162 170 131 54 27 39 56 70 50 48 84 92 76 51 59 79 70 62 61 97 185 189 154 77 46 55 61 63 47 51 91 92 74 60 87 122 103 79 84 118 208 218 157 89 66 72 65 64 46 54 101 103 78 49 84 146 122 87 95 113 180 196 127 69 63 89 91 92 64 68 120 120 73 47 77 148 118 85 99 95 125 130 84 51 71 125 127 109 73 69 115 129 76"

myID = 1
gameMap = GameMap(size_string, prod_string, map_string)

dij = Dijkstra(gameMap)

# this is attempting to find the best path after some frame
(future_value, new_path) = dij.get_path_for_future(
    gameMap.contents[5][10],
    Square(-1,-1,0,0,0),
    160)

print(future_value)
for path in new_path:
    print(path)
