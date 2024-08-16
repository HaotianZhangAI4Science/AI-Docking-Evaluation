#!/bin/bash

# read input.csv
while IFS=, read -r protein_path ligand; do
    # extract the path
    protein_file="${protein_path##*/}"
    pdb_id="${pdb_id%%_*}"
    ligand_file="ligand.csv"

    # temp file for ligand
    echo "protein_path,ligand" > $ligand_file
    echo "$protein_path,$ligand" >> $ligand_file

    # perform docking
    echo "docking $protein_file $ligand_file"
    ./docking_single.sh "$protein_path" "$ligand_file" "$pdb_id"

done < <(tail -n +2 input.csv)
rm ligand.csv
echo "Docking complete"