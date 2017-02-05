#!/usr/bin/env bash

FILE=250

cd profiles
pyprof2calltree -i "profile-$FILE.pyprof" -k