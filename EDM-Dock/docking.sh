#!/bin/bash
python scripts/dock.py \
  --weight_path './ckpt' \
  --config_path './configs/config.yml' \
  --result_path './posebusters_results' \
  --dataset_path '/mnt/data/posebusters_edmdock'
