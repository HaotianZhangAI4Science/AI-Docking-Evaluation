
# DynamicBind
Refer to the original paper or `DynamicBind-README.md` for more details.

## Installation

Create a new environment for inference. While in the project directory run 

    conda env create -f environment.yml

Or you setup step by step:

    conda create -n dynamicbind python=3.10

Activate the environment

    conda activate dynamicbind

Install
    
    conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia
    conda install -c conda-forge rdkit
    conda install pyg  pyyaml  biopython -c pyg
    pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-2.0.0+cu117.html
    pip install e3nn  fair-esm spyrmsd

Create a new environment for structural Relaxation.

    conda create --name relax python=3.8

Activate the environment

    conda activate relax

Install

    conda install -c conda-forge openmm pdbfixer libstdcxx-ng openmmforcefields openff-toolkit ambertools=22 compilers biopython

Download and unzip the workdir.zip containing the model checkpoint form https://zenodo.org/records/10137507, v2 is contained here https://zenodo.org/records/10183369.

## Test the Pre-trained Model on Posebusters

#### Step 1: Go to the `posebusters` folder
```sh
cd posebusters
```
#### Step 2: Running `ori2inp.ipynb`
You need to modify the path in the script by yourself. An example is shown in the notebook.

#### Step 3: Perform Docking Process
```sh
./docking.sh # just run this command
# below is the content of docking_single.sh
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
```
This process takes a rather long period. You may consider using `nohup` to run the script in the background. Also, the docking process doesn't require structural relaxation by default, you can simply remove `--no_relax` to access the structural relaxation. More information can be found in the original `DynamicBind-README.md`.

#### Step 4: Extract Poses by `extract_pose.ipynb`
The final docked poses will be saved in the folder `./posebusters/dynamicbind` as `[ID]_docked.sdf and [ID]_docked.pdb` in `[ID]` subdirs.

#### Step 5: Calculate RMSD
You can complete this process by running the notebook `rmsd_unaligned.ipynb` after updating the path in the script. We use the package `networkx` to align the graphs generated from the docked and real poses.

## Claims
DynamicBind is a model that does not treat protein
molecules as a rigid body, which means while we calculate the rmsd between the docked ligand pose and the real ligand pose, we do not fully align the two proteins. However, we can still use the rmsd to compare the docked ligand pose and the real ligand pose as a rough indicator of the quality of the docking process.