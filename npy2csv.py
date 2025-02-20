import numpy as np
import csv
import os

def npy_to_csv(npy_file: str, csv_file: str):
    # 载入 .npy 文件
    data = np.load(npy_file, allow_pickle=True)

    # 打开文件并创建 csv.writer
    with open(csv_file, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # 写入表头
        writer.writerow(["Index", "Energy (eV)", "Step", "Force (au)", "Coordinates", "Species"])

        # 遍历数据并写入 CSV
        for idx, steps in enumerate(data):
            for step_data in steps:
                # 获取每个步骤的数据
                energy = step_data['energy'] if step_data['energy'] is not None else "N/A"
                step = step_data['step'] if step_data['step'] is not None else "N/A"
                force = step_data['force'] if step_data['force'] is not None else "N/A"
                coordinates = step_data['coordinates']
                species = step_data['species']

                # 格式化原子坐标和元素
                coords_str = "; ".join([f"({x[0]}, {x[1]}, {x[2]})" for x in coordinates])
                species_str = "; ".join(species)

                # 写入一行数据
                writer.writerow([idx, energy, step, force, coords_str, species_str])

    print(f"Data successfully written to {csv_file}")

if __name__ == "__main__":
    # 读取用户输入的文件路径
    npy_file = input("Enter the .npy file path: ").strip()
    if not os.path.isfile(npy_file):
        print("The provided .npy file path is invalid.")
        exit(1)

    # 生成 CSV 文件的路径
    csv_file = npy_file.replace('.npy', '.csv')

    # 调用函数将数据从 .npy 转换为 .csv
    npy_to_csv(npy_file, csv_file)
