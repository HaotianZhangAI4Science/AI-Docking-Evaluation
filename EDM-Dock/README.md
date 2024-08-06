
# EDM-Dock
Refer to the original paper or `EDM-Dock-README.MD` for more details.

## Installation

```sh
git clone https://github.com/HaotianZhangAI4Science/AI-Docking-Evaluation.git
cd AI-Docking-Evaluation/EDM-Dock
conda env create -f environment.yaml -n edm-dock
conda activate edm-dock
python setup.py install
```

## Test the Pre-trained Model on Posebusters
#### Step 1: Prepare a Dataset in the Following Format
```sh
posebusters_dataset_path/
    sys1/
        protein.pdb
        ligand.sdf
        box.csv
    sys2/
        protein.pdb
        ligand.sdf
        box.csv
    ...
```
The `box.csv` file defines the binding site box and should contain six comma-separated values:
```sh
center_x, center_y, center_z, width_x, width_y, width_z
```
You can complete this process by running `./posebusters.sh` after updating the path in the shell script.

#### Step 2: Prepare the Features Using the Provided Shell Script
```sh
./prepare.sh # Details can be found in the shell script
```

#### Step 3: Download DGSOL
Since DGSOL does not have an MIT license, its code is included in a separate repository (https://github.com/MatthewMasters/DGSOL.git). Once you have downloaded DGSOL, update the path at the top of `edmdock/utils/dock.py` to reflect its location on your system. Remember to rebuild the package by running `python setup.py install`.

#### Step 4: Run Docking Using the Provided Shell Script
```sh
./docking.sh # Details can be found in the shell script
```
The final docked poses will be saved in the folder `./posebusters_results` as `[ID]_docked.pdb`.

## Claims
Some code changes were made to ensure compatibility with the Posebusters dataset.

**In `./EDM-Dock/edmdock/utils/feats.py`, Line 186**
```python
# Original Code
pocket_types = np.array([RESIDUES[res.name] for res in pocket.residues])
```

```python
# Avoid Unknown Residues While Preparing Dataset
pocket_types = np.array([RESIDUES.get(res.name, 20) for res in pocket.residues])
```
