#!/usr/bin/env bash

FILE=150

cd profiles
pyprof2calltree -i "profile-$FILE.pyprof" -k