import os
import shutil
from glob import glob
from rdkit import Chem
from rdkit.Chem import AllChem
import argparse

def process_files(source_dir, target_dir, box_length, box_width, box_height):
    # 创建目标目录（如果不存在）
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # 遍历源目录中的每个子目录
    for pdb_folder in glob(os.path.join(source_dir, '*')):
        if os.path.isdir(pdb_folder):
            # 获取文件夹名称
            folder_name = os.path.basename(pdb_folder)
            
            # 定义文件路径
            ligand_sdf = os.path.join(pdb_folder, f'{folder_name}_ligand.sdf')
            protein_pdb = os.path.join(pdb_folder, f'{folder_name}_protein.pdb')
            
            # 定义目标文件夹
            target_subfolder = os.path.join(target_dir, folder_name)
            if not os.path.exists(target_subfolder):
                os.makedirs(target_subfolder)
            
            # 复制并重命名文件
            if os.path.exists(ligand_sdf):
                shutil.copy(ligand_sdf, os.path.join(target_subfolder, 'ligand.sdf'))
            if os.path.exists(protein_pdb):
                shutil.copy(protein_pdb, os.path.join(target_subfolder, 'protein.pdb'))
            
            # 读取配体的坐标，计算几何中心
            if os.path.exists(ligand_sdf):
                suppl = Chem.SDMolSupplier(ligand_sdf)
                molecule = suppl[0]  # 假设 SDF 文件中只有一个分子
                conformer = molecule.GetConformer()
                coords = [conformer.GetAtomPosition(i) for i in range(molecule.GetNumAtoms())]
                x_center = sum(coord.x for coord in coords) / len(coords)
                y_center = sum(coord.y for coord in coords) / len(coords)
                z_center = sum(coord.z for coord in coords) / len(coords)
                
                # 生成box.csv文件
                box_csv_path = os.path.join(target_subfolder, 'box.csv')
                with open(box_csv_path, 'w') as box_file:
                    box_file.write(f'{x_center},{y_center},{z_center},{box_length},{box_width},{box_height}\n')

    print('All Finished!')

def main():
    parser = argparse.ArgumentParser(description='Process ligand and protein files and generate box configuration.')
    parser.add_argument('--source_dir', type=str, required=True, help='Path to the source directory.')
    parser.add_argument('--target_dir', type=str, required=True, help='Path to the target directory.')
    parser.add_argument('--box_length', type=float, default=22.5, help='Length of the box.')
    parser.add_argument('--box_width', type=float, default=22.5, help='Width of the box.')
    parser.add_argument('--box_height', type=float, default=22.5, help='Height of the box.')

    args = parser.parse_args()

    process_files(args.source_dir, args.target_dir, args.box_length, args.box_width, args.box_height)

if __name__ == '__main__':
    main()