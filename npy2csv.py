import os
import sys
import csv
import numpy as np

def npy_to_csv(npy_file: str, csv_file: str):
    """
    将 .npy 数据转换为 .csv，并包含：
      - Energy (Ha)
      - Step
      - Max Force (au)
      - Coordinates (au)
      - Species
      - Forces (au)
      - Orb (eV)
    """
    data = np.load(npy_file, allow_pickle=True)

    with open(csv_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # 写入表头，Orb (eV) 中间带空格
        writer.writerow([
            "FileIndex",
            "Energy (Ha)",
            "Step",
            "Max Force (au)",
            "Coordinates (au)",
            "Species",
            "Forces (au)",
            "Orb (eV)"
        ])

        for file_idx, steps in enumerate(data):
            for step_data in steps:
                energy    = step_data.get('energy (Ha)', "N/A")
                step_num  = step_data.get('step',            "N/A")
                max_force = step_data.get('max force (au)',  "N/A")
                coords    = step_data.get('coordinates (au)', [])
                species   = step_data.get('species',         [])
                forces    = step_data.get('forces (au)',     [])
                orbitals  = step_data.get('orb (eV)',        [])

                # 格式化为字符串；clean_num 已在提取时生效
                coords_str   = "; ".join(f"({x}, {y}, {z})" for x, y, z in coords)
                species_str  = "; ".join(species)
                forces_str   = "; ".join(f"({fx}, {fy}, {fz})" for fx, fy, fz in forces)
                orb_str      = "; ".join(f"({state}, {ev}, {occ})" 
                                         for state, ev, occ in orbitals)

                writer.writerow([
                    file_idx,
                    energy,
                    step_num,
                    max_force,
                    coords_str,
                    species_str,
                    forces_str,
                    orb_str
                ])

    print(f"Data successfully written to {csv_file}")


if __name__ == "__main__":
    npy_file = input("Enter the .npy file name: ").strip()
    if not os.path.isfile(npy_file):
        print("The provided .npy file name is invalid.")
        sys.exit(1)

    csv_file = os.path.splitext(npy_file)[0] + '.csv'
    npy_to_csv(npy_file, csv_file)
