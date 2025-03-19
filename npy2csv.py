import numpy as np
import csv
import os

def npy_to_csv(npy_file: str, csv_file: str):
    """将 .npy 数据转换为 .csv 并包含 forces（原子受力）"""
    data = np.load(npy_file, allow_pickle=True)

    with open(csv_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # 写入表头（带单位）
        writer.writerow(["Index", "Energy (eV)", "Step", "Max Force (au)", "Coordinates (au)", "Species", "Forces (au)"])

        # 遍历数据并写入 CSV
        for idx, steps in enumerate(data):
            for step_data in steps:
                energy = step_data.get('energy (eV)', "N/A")
                step = step_data.get('step', "N/A")
                max_force = step_data.get('max force (au)', "N/A")
                coordinates = step_data.get('coordinates (au)', [])
                species = step_data.get('species', [])
                forces = step_data.get('forces (au)', [])

                # 格式化原子坐标和元素
                coords_str = "; ".join([f"({x[0]}, {x[1]}, {x[2]})" for x in coordinates])
                species_str = "; ".join(species)

                # **新增**: 格式化 forces
                forces_str = "; ".join([f"({f[0]}, {f[1]}, {f[2]})" for f in forces])

                # 写入 CSV
                writer.writerow([idx, energy, step, max_force, coords_str, species_str, forces_str])

    print(f"Data successfully written to {csv_file}")

if __name__ == "__main__":
    npy_file = input("Enter the .npy file name: ").strip()
    if not os.path.isfile(npy_file):
        print("The provided .npy file name is invalid.")
        exit(1)

    csv_file = npy_file.replace('.npy', '.csv')
    npy_to_csv(npy_file, csv_file)
