#!/bin/bash
python posebusters.py \
--source_dir '/mnt/data/posebusters/posebusters_benchmark_set' \  # path to the posebusters dataset
--target_dir '/mnt/data/posebusters_edmdock' \                    # path to the target directory (unprepared posebusters dataset)
--box_length 22.5 \                                               # box length,width and height
--box_width 22.5 \
--box_height 22.5