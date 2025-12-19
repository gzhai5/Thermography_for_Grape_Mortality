#!/bin/bash


for lr in 0.005 0.001 0.0005 0.0001
do
    python vivit-run.py --lr $lr
done