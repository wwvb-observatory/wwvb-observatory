#!/bin/sh
mkdir -p summary/"`dirname "$1"`"
python3 src/stats.py data/"$1"-*/*.txt > summary/"$1".txt
