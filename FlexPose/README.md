
# FlexPose
Refer to the original paper or `FlexPose-README.md` for more details.

## Installation
FlexPose is implemented in PyTorch. All basic dependencies are listed in `requirements.txt` and most of them can be easily installed with pip install. We provide tested installation commands in install_cmd.txt for your reference.

Install FlexPose pacakge
`pip install -e .`

## Test the Pre-trained Model on Posebusters
#### Step 1: Convert SDF Files to Mol2 Files
```sh
./sdf2mol2.sh # obabel is required
```

#### Step 2: Generate CSV File for Batch Prediction

You can complete this process by running the notebook `write_csv.ipynb` after updating the path in the script.

#### Step 3: Run Docking Using the Provided Shell Script
```sh
./docking.sh # Details can be found in the shell script
```
The final docked poses will be saved in the folder `./posebusters_benchmark/docking_results` as `[ID].sdf and [ID].mol2`.

#### Step 4: Calculate RMSD without Alignment

The process is autocompleted in step3.

## Claims
Fabind is a blind docking model, so we calculate the RMSD between the ligand in the ground truth and the ligand in the docked pose without alignment. If certain docked poses cannot pass the rdkit filter, we will not calculate the RMSD and replace the RMSD value with -1.
