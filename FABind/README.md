
# FABind
Refer to the original paper or `FABIND-README.md` for more details.

## Installation

```sh
conda create --name fabind python=3.8
conda activate fabind
conda install pytorch==1.12.0 torchvision==0.13.0 torchaudio==0.12.0 cudatoolkit=11.3 -c pytorch
pip install https://data.pyg.org/whl/torch-1.12.0%2Bcu113/torch_cluster-1.6.0%2Bpt112cu113-cp38-cp38-linux_x86_64.whl
pip install https://data.pyg.org/whl/torch-1.12.0%2Bcu113/torch_scatter-2.1.0%2Bpt112cu113-cp38-cp38-linux_x86_64.whl
pip install https://data.pyg.org/whl/torch-1.12.0%2Bcu113/torch_sparse-0.6.15%2Bpt112cu113-cp38-cp38-linux_x86_64.whl 
pip install https://data.pyg.org/whl/torch-1.12.0%2Bcu113/torch_spline_conv-1.2.1%2Bpt112cu113-cp38-cp38-linux_x86_64.whl
pip install https://data.pyg.org/whl/torch-1.12.0%2Bcu113/pyg_lib-0.2.0%2Bpt112cu113-cp38-cp38-linux_x86_64.whl
pip install torch-geometric==2.4.0
pip install torchdrug==0.1.2 torchmetrics==0.10.2 tqdm mlcrate pyarrow accelerate Bio lmdb fair-esm tensorboard
pip install fair-esm
pip install rdkit-pypi==2021.03.4
conda install -c conda-forge openbabel # install openbabel to save .mol2 file and .sdf file at the same time
```

## Test the Pre-trained Model on Posebusters
#### Step 1: Convert SDF Files to Mol2 Files
```sh
./sdf2mol2.sh # obabel is required
```

#### Step 2: Prepare a Dataset in the Following Format
```sh
posebusters_fabind/
    ligands.csv
    pdb_files/
        [ID1].pdb
        [ID2].pdb
        ...
    gt_mol_files/
        [ID1]/
            [ID1]_ligand.mol2
            [ID1]_ligand.sdf
        [ID2]/
            [ID2]_ligand.mol2
            [ID2]_ligand.sdf
        ...
```
You can complete this process by running the notebook `prepare_fabind.ipynb` after updating the path in the script.

#### Step 3: Run Docking Using the Provided Shell Script
```sh
./docking.sh # Details can be found in the shell script
```
The final docked poses will be saved in the folder `./posebusters_benchmark/docking_results` as `[ID].sdf and [ID].mol2`.

#### Step 4: Calculate RMSD
You can complete this process by running the notebook `rmsd_unaligned.ipynb` after updating the path in the script. We use the package `networkx` to align the graphs generated from the docked and real poses.

## Claims
Fabind is a blind docking model, so we calculate the RMSD between the ligand in the ground truth and the ligand in the docked pose without alignment. If certain docked poses cannot pass the rdkit filter, we will not calculate the RMSD by `rmsd_unaligned.ipynb` and replace the RMSD value with -1. Also, we write a script `rmsd_unaligned_nordkit.ipynb` to calculate the RMSD without rdkit filter.
