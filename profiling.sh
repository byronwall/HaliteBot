#!/usr/bin/env bash

FILE=50

cd profiles
pyprof2calltree -i "profile-$FILE.pyprof" -k