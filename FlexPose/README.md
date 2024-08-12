
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
The final docked poses will be saved in the folder `./posebusters_benchmark` as `[idx].pdb` which includes the ligand pose in the pdb file.

#### Step 4: Calculate RMSD without Alignment

The process is autocompleted in step3. You may notice some of the rows have empty RMSD value. This is because the docking process failed due to some reasons (shown in claims) and the RMSD value is not calculated. (Total access rate is around 52%)

## Claims
We test the FlexPose as a site-specific docking model, but actually the model generates the protein-ligand complex's structure directly. Also, as mentioned above, the docking process failed in some cases. The reasons are listed below:

1. Unrecognized residue types:
   - Several non-standard amino acids were not recognized by the docking model
   - Examples include MLY, MHS, AGM, SMC, I2M, MGN, GL3, HIC, KCX, TYS, PTR, CME, and others

2. RTF (Residue Topology File) constraint issues:
   - RTF restraints were not found in the atoms list for certain residues
   - This affected residues with indices 13 and 1

3. Chain ID problems:
   - Multiple chains in the model did not have unique chain IDs

4. Atom naming conflicts:
   - Inability to add atoms named 'CS' to ResidueType pdb_SMC due to existing atoms with the same name
   - Similar issue with atoms named 'OP1' in pdb_LLP residue type

5. Assertion failures:
   - An assertion `! found_aa_difference` failed, indicating unexpected amino acid differences

6. Residue definition incompleteness:
   - Some residue types were treated as rigid bodies due to lack of proper definitions

7. Unrecognized ligand components:
   - Certain ligand residues (e.g., UDP) were not recognized and were treated using 'AutoModel' building

8. Potential structural inconsistencies:
   - Warnings about residues or atoms not being found in expected lists or structures

9. Possible force field incompatibilities:
   - Indications that some residues or atoms might not be properly parameterized in the current force field

10. File format and input structure issues:
    - Suggestions of potential problems with the input PDB or molecule files

Note: These issues were reported by the docking software and may require manual intervention or adjustment of input files to resolve.