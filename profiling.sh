#!/usr/bin/env bash

FILE=200

cd profiles
pyprof2calltree -i "profile-$FILE.pyprof" -k