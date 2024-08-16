#!/bin/bash
export MKL_THREADING_LAYER=GNU
python ./../run_single_protein_inference.py "$1" "$2" \
    --savings_per_complex 40 \
    --inference_steps 20 \
    --header "$3" \
    --python /mnt/data/miniforge3/envs/dynamicbind/bin/python \
    --relax_python /mnt/data/miniforge3/envs/relax/bin/python \
    --paper \
    --no_relax
