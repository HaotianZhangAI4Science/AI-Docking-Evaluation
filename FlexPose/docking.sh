#!/bin/bash
export LD_LIBRARY_PATH="/mnt/data/miniforge3/envs/FlexPose/lib:$LD_LIBRARY_PATH" #cuda_path
python demo.py
