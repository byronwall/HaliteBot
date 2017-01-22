import os
import hlt
import logging
import time
import cProfile
import argparse
from HaliteBotCode import *
import time

start_time = time.time()

size_string = "10 10"
prod_string = "2 2 3 7 5 3 3 2 2 2 3 3 3 4 4 6 7 4 3 2 3 2 2 4 5 6 6 5 3 2 2 2 2 3 4 4 4 4 2 2 2 2 1 1 2 4 7 4 2 2 2 2 2 3 3 5 7 3 2 2 2 3 4 7 6 4 4 3 3 3 2 3 5 6 6 5 4 2 2 3 2 2 4 4 4 4 3 2 2 2 2 2 4 7 4 2 1 1 2 2"
map_string = "7 0 1 2 44 0 1 1 47 0 127 127 80 35 42 52 71 101 88 92 148 184 97 46 35 46 60 61 67 89 122 171 101 81 71 88 64 59 54 81 99 136 118 91 86 147 97 81 79 107 77 90 116 84 63 92 71 112 114 118 92 88 101 71 52 42 35 80 127 127 89 67 61 60 46 35 46 97 184 148 81 54 59 64 88 71 81 101 171 122 107 79 81 97 147 86 91 118 136 99 118 114 112 71 92 63 84 116 90 77"

size_string = "20 20"
prod_string = "0 0 0 1 0 0 0 1 2 2 1 1 1 1 1 1 0 1 1 1 1 0 0 1 0 0 1 2 2 2 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1 2 2 2 1 1 2 2 2 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 2 1 1 2 1 1 1 1 1 1 1 0 0 1 1 1 2 3 3 3 2 1 1 1 1 1 1 1 1 1 1 0 1 1 1 2 2 3 3 3 1 1 1 1 1 1 1 2 2 2 1 1 1 1 2 2 2 3 3 2 1 0 1 1 1 2 2 2 2 2 1 1 1 1 2 2 3 3 4 3 1 0 0 1 1 2 2 3 2 1 1 1 1 1 2 3 3 4 6 4 1 0 0 1 1 1 2 3 2 1 1 0 1 1 1 2 2 4 6 4 1 0 0 1 1 1 2 3 2 1 1 0 1 1 1 2 2 4 6 4 1 0 0 1 1 2 2 3 2 1 1 1 1 1 2 3 3 4 6 4 1 0 1 1 1 2 2 2 2 2 1 1 1 1 2 2 3 3 4 3 1 1 1 1 1 1 1 2 2 2 1 1 1 1 2 2 2 3 3 2 2 1 1 1 1 1 1 1 1 1 1 0 1 1 1 2 2 3 3 3 2 1 1 2 1 1 1 1 1 1 1 0 0 1 1 1 2 3 3 3 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 1 1 1 1 1 0 1 2 2 2 1 1 2 2 2 1 1 1 1 1 1 0 0 1 0 0 1 2 2 2 1 1 1 1 1 1 1 1 1 1 0 0 0 1 0 0 0 1 2 2 1 1 1 1 1 1 0 1 1 1"
map_string = "110 0 1 1 179 0 1 2 109 0 47 77 148 118 85 99 95 125 130 84 51 71 125 127 109 73 69 115 129 76 49 84 146 122 87 95 113 180 196 127 69 63 89 91 92 64 68 120 120 73 60 87 122 103 79 84 118 208 218 157 89 66 72 65 64 46 54 101 103 78 51 59 79 70 62 61 97 185 189 154 77 46 55 61 63 47 51 91 92 74 45 34 48 59 62 52 84 162 170 131 54 27 39 56 70 50 48 84 92 76 39 23 34 54 59 40 56 112 128 94 39 25 37 50 59 44 52 88 104 78 34 15 21 39 49 42 58 89 89 73 45 40 51 57 52 50 68 96 114 82 26 13 21 34 44 51 77 97 88 92 73 60 61 67 58 57 74 99 113 71 17 17 29 42 44 52 77 108 116 123 82 65 78 98 80 63 68 72 70 39 14 16 28 40 41 51 69 120 155 161 94 78 98 118 91 52 46 54 52 28 14 16 28 40 41 51 69 120 155 161 94 78 98 118 91 52 46 54 52 28 17 17 29 42 44 52 77 108 116 123 82 65 78 98 80 63 68 72 70 39 26 13 21 34 44 51 77 97 88 92 73 60 61 67 58 57 74 99 113 71 34 15 21 39 49 42 58 89 89 73 45 40 51 57 52 50 68 96 114 82 39 23 34 54 59 40 56 112 128 94 39 25 37 50 59 44 52 88 104 78 45 34 48 59 62 52 84 162 170 131 54 27 39 56 70 50 48 84 92 76 51 59 79 70 62 61 97 185 189 154 77 46 55 61 63 47 51 91 92 74 60 87 122 103 79 84 118 208 218 157 89 66 72 65 64 46 54 101 103 78 49 84 146 122 87 95 113 180 196 127 69 63 89 91 92 64 68 120 120 73 47 77 148 118 85 99 95 125 130 84 51 71 125 127 109 73 69 115 129 76"

size_string = "30 30"
prod_string = "2 1 1 1 1 1 1 2 3 3 4 3 3 3 4 3 2 2 2 2 1 2 3 4 4 3 3 3 4 4 3 2 2 1 1 2 2 3 4 4 3 3 2 2 3 3 1 1 1 1 1 2 4 5 5 4 4 5 5 5 3 2 2 2 2 2 3 4 5 5 4 3 2 2 3 2 1 1 1 1 1 2 4 5 5 4 4 4 4 4 2 2 1 1 1 1 2 3 5 6 5 3 3 3 3 3 2 1 1 1 1 2 3 4 3 3 2 2 2 3 2 1 1 1 1 1 1 2 4 4 4 3 2 2 3 2 2 1 1 1 1 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 2 2 3 3 2 2 2 3 2 2 1 1 1 1 2 2 2 1 1 1 2 2 2 2 1 1 1 1 1 1 1 2 2 2 2 2 2 3 3 2 2 1 1 1 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 1 1 2 4 4 3 3 3 3 3 3 3 2 1 1 1 1 2 1 1 2 1 1 1 2 2 2 3 3 3 2 2 4 6 6 6 5 4 4 5 5 4 3 2 2 2 2 2 2 2 2 1 1 1 1 2 2 3 4 4 4 4 5 7 6 5 5 4 4 5 6 6 4 4 3 3 3 3 3 2 2 1 1 1 1 1 2 3 4 5 5 5 6 6 6 5 5 4 4 6 8 5 5 4 4 3 3 3 3 3 2 2 2 2 2 2 2 3 3 4 4 4 4 5 5 4 4 4 4 5 7 3 3 3 2 2 2 2 2 3 3 3 3 3 3 2 3 4 4 3 3 3 4 4 4 3 3 3 3 3 4 2 1 1 1 1 1 1 2 2 3 3 2 3 3 3 4 6 6 4 3 4 5 5 4 3 3 3 3 3 2 1 1 1 1 1 1 1 2 3 4 2 2 2 2 3 6 9 8 5 4 5 6 6 4 3 3 3 4 3 2 1 1 1 1 1 1 1 2 3 4 2 2 2 2 3 6 9 8 5 4 5 6 6 4 3 3 3 4 3 2 2 1 1 1 1 1 1 2 2 3 3 2 3 3 3 4 6 6 4 3 4 5 5 4 3 3 3 3 3 2 3 3 3 2 2 2 2 2 3 3 3 3 3 3 2 3 4 4 3 3 3 4 4 4 3 3 3 3 3 4 5 5 4 4 3 3 3 3 3 2 2 2 2 2 2 2 3 3 4 4 4 4 5 5 4 4 4 4 5 7 6 4 4 3 3 3 3 3 2 2 1 1 1 1 1 2 3 4 5 5 5 6 6 6 5 5 4 4 6 8 4 3 2 2 2 2 2 2 2 2 1 1 1 1 2 2 3 4 4 4 4 5 7 6 5 5 4 4 5 6 3 2 1 1 1 1 2 1 1 2 1 1 1 2 2 2 3 3 3 2 2 4 6 6 6 5 4 4 5 5 2 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 1 1 2 4 4 3 3 3 3 3 3 2 1 1 1 1 1 1 1 2 2 2 2 2 2 3 3 2 2 1 1 1 2 2 2 2 2 2 2 2 2 2 1 1 1 1 1 1 2 2 3 3 2 2 2 3 2 2 1 1 1 1 2 2 2 1 1 1 2 2 2 2 1 1 1 1 1 1 2 4 4 4 3 2 2 3 2 2 1 1 1 1 2 2 2 2 2 2 2 2 2 2 2 1 1 1 1 2 3 5 6 5 3 3 3 3 3 2 1 1 1 1 2 3 4 3 3 2 2 2 3 3 2 2 2 2 2 3 4 5 5 4 3 2 2 3 2 1 1 1 1 1 2 4 5 5 4 4 4 4 4 3 2 2 1 1 2 2 3 4 4 3 3 2 2 3 3 1 1 1 1 1 2 4 5 5 4 4 5 5 5 2 1 1 1 1 1 1 2 3 3 4 3 3 3 4 3 2 2 2 2 1 2 3 4 4 3 3 3 4 4"
map_string = "225 0 1 1 449 0 1 2 224 0 176 146 145 142 129 102 111 135 136 112 67 52 62 82 91 89 68 54 48 37 26 36 60 74 76 75 83 120 185 209 137 101 99 100 95 93 121 133 114 89 56 45 52 65 66 65 53 46 42 33 29 47 81 105 106 95 92 116 168 181 105 70 64 61 59 73 111 117 91 73 59 54 55 59 54 52 41 34 33 32 31 53 95 121 117 103 93 97 129 145 89 54 52 48 44 54 79 79 67 66 70 68 66 62 50 46 39 30 30 32 36 61 111 135 123 110 102 99 122 136 71 36 33 31 30 37 52 49 46 51 54 57 68 73 60 58 55 39 34 38 49 79 127 133 102 78 71 79 108 121 73 33 24 22 24 30 39 35 33 38 37 40 58 72 66 68 67 49 42 49 65 96 132 119 80 52 47 66 103 123 70 34 20 18 20 23 28 25 23 28 31 35 49 58 50 51 55 46 43 52 73 99 115 90 62 42 37 53 85 107 62 32 18 18 22 22 21 21 21 27 33 35 42 44 35 36 45 39 33 41 61 86 94 71 58 49 40 49 73 89 63 32 20 22 27 27 26 27 27 28 28 25 28 30 30 36 46 39 30 33 44 64 77 67 74 83 72 73 92 95 64 32 25 25 28 28 30 38 40 35 25 17 18 25 37 45 46 39 36 37 36 45 57 59 83 113 110 113 130 112 84 44 35 30 27 24 29 44 62 59 39 21 17 27 46 51 42 34 35 37 37 46 54 44 55 85 108 145 181 154 98 61 55 46 38 37 44 67 105 105 74 41 27 33 50 50 35 27 27 30 38 57 70 45 35 55 90 141 184 166 75 71 81 74 64 69 80 111 168 174 138 86 59 66 91 85 51 32 25 27 41 64 81 50 29 39 62 90 112 105 62 79 95 91 84 91 95 124 190 213 181 121 95 121 168 156 94 50 31 27 39 64 82 50 29 35 47 53 60 62 66 90 97 84 75 80 87 120 190 230 188 123 109 160 225 205 120 58 31 25 36 62 76 45 27 33 40 36 41 52 66 90 97 84 75 80 87 120 190 230 188 123 109 160 225 205 120 58 31 25 36 62 76 45 27 33 40 36 41 52 62 79 95 91 84 91 95 124 190 213 181 121 95 121 168 156 94 50 31 27 39 64 82 50 29 35 47 53 60 62 75 71 81 74 64 69 80 111 168 174 138 86 59 66 91 85 51 32 25 27 41 64 81 50 29 39 62 90 112 105 98 61 55 46 38 37 44 67 105 105 74 41 27 33 50 50 35 27 27 30 38 57 70 45 35 55 90 141 184 166 84 44 35 30 27 24 29 44 62 59 39 21 17 27 46 51 42 34 35 37 37 46 54 44 55 85 108 145 181 154 64 32 25 25 28 28 30 38 40 35 25 17 18 25 37 45 46 39 36 37 36 45 57 59 83 113 110 113 130 112 63 32 20 22 27 27 26 27 27 28 28 25 28 30 30 36 46 39 30 33 44 64 77 67 74 83 72 73 92 95 62 32 18 18 22 22 21 21 21 27 33 35 42 44 35 36 45 39 33 41 61 86 94 71 58 49 40 49 73 89 70 34 20 18 20 23 28 25 23 28 31 35 49 58 50 51 55 46 43 52 73 99 115 90 62 42 37 53 85 107 73 33 24 22 24 30 39 35 33 38 37 40 58 72 66 68 67 49 42 49 65 96 132 119 80 52 47 66 103 123 71 36 33 31 30 37 52 49 46 51 54 57 68 73 60 58 55 39 34 38 49 79 127 133 102 78 71 79 108 121 89 54 52 48 44 54 79 79 67 66 70 68 66 62 50 46 39 30 30 32 36 61 111 135 123 110 102 99 122 136 105 70 64 61 59 73 111 117 91 73 59 54 55 59 54 52 41 34 33 32 31 53 95 121 117 103 93 97 129 145 137 101 99 100 95 93 121 133 114 89 56 45 52 65 66 65 53 46 42 33 29 47 81 105 106 95 92 116 168 181 176 146 145 142 129 102 111 135 136 112 67 52 62 82 91 89 68 54 48 37 26 36 60 74 76 75 83 120 185 209"

myID = 1
gameMap = GameMap(size_string, prod_string, map_string)

dij = Dijkstra(gameMap, myID)
value,path = dij.get_path_with_strength(gameMap.contents[8][15], 5, 5)

if False:
    value,path = dij.do_genetic_search(gameMap.contents[5][10], 150)

print(value)
print("".join(map(str, path)))

print(time.time() - start_time)

exit()

# this is attempting to find the best path after some frame
(future_value, new_path) = dij.get_path_for_future(
    gameMap.contents[5][10],
    Square(-1, -1, 0, 0, 0),
    200)

print(future_value)
for path in new_path:
    print(path)

print(time.time() - start_time)
