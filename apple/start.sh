#!/bin/bash

while true; do
    python main.py --mode acquire
    echo "main.py crashed with exit code $?.  Respawning.." >&2
    sleep 1
done