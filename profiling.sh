#!/usr/bin/env bash

FILE=350

cd profiles
pyprof2calltree -i "profile-$FILE.pyprof" -k