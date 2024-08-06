#!/bin/bash
index_csv=/mnt/data/posebusters_fabind/ligands.csv
pdb_file_dir=/mnt/data/posebusters_fabind/pdb_files
num_threads=1
save_pt_dir=/mnt/data/posebusters_fabind/temp_files
save_mols_dir=${save_pt_dir}/mol
ckpt_path=../ckpt/best_model.bin
output_dir=./../posebusters_benchmark/docking_results

cd fabind

echo "======  preprocess molecules  ======"
python inference_preprocess_mol_confs.py --index_csv ${index_csv} --save_mols_dir ${save_mols_dir} --num_threads ${num_threads}

echo "======  preprocess proteins  ======"
python inference_preprocess_protein.py --pdb_file_dir ${pdb_file_dir} --save_pt_dir ${save_pt_dir}

echo "======  inference begins  ======"
python fabind_inference.py \
    --ckpt ${ckpt_path} \
    --batch_size 4 \
    --seed 128 \
    --test-gumbel-soft \
    --redocking \
    --post-optim \
    --write-mol-to-file \
    --sdf-output-path-post-optim ${output_dir} \
    --index-csv ${index_csv} \
    --preprocess-dir ${save_pt_dir} \
    --sdf-to-mol2