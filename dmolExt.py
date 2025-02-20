#!Jackeyli@240715
# Updated by leonehuo@gmail.com on 2025/02/20
# 1. 读取当前文件夹下所有以 dmol_3 开始的文件夹中，.outmol 结尾的文件
# 2. 读取能量、原子结构（坐标 + 元素）、Step 数、最大力
# 3. 整合数据，保存为 .npy 格式

import os
import sys
import numpy as np
import re

class read_outputdmol():
    # 初始化，传入输出文件路径
    def __init__(self, outdmol_path: str) -> None:
        self.outdmol_path = outdmol_path  # 保存文件路径

    # 获取文件中的原子数量
    def atom_number(self) -> str:
        with open(self.outdmol_path) as f:
            for line in f:
                if 'N_atoms =' in line:  # 查找原子数
                    return int(line.split()[2])  # 返回原子数
        return None

    # 解析输出文件，提取每一步的计算数据
    def Iron_step(self) -> list:
        all_steps_data = []  # 存储所有步骤数据
        atom_n = self.atom_number()  # 获取原子数量

        with open(self.outdmol_path) as f:
            lines = f.readlines()

        # 每个步骤的数据结构
        step_data = {
            'energy': None,  # 能量
            'coordinates': [],  # 坐标
            'species': [],  # 元素种类
            'step': None,  # 步数
            'force': None  # 最大力
        }

        # 循环读取文件每一行
        for i, line in enumerate(lines):
            # **1. 读取 SCF 总能量**
            if 'Total Energy           Binding E       Cnvgnce     Time   Iter' in line:
                for j in range(i + 1, len(lines)):
                    energy_line = lines[j].strip()
                    if 'Message: SCF converged' in energy_line:
                        # 获取总能量
                        energy_value = lines[j - 1].split()[1]  
                        if energy_value.endswith("Ha"):
                            energy_value_eV = float(energy_value[:-2]) * 27.212  # 转换为 eV
                            step_data['energy'] = energy_value_eV
                        break
                    elif 'Error: SCF iterations not converged' in energy_line:
                        return all_steps_data  # 如果SCF不收敛，跳过该步

            # **2. 读取原子坐标和元素种类**
            elif "df              ATOMIC  COORDINATES (au)" in line:
                output_coordinate = lines[i + 2:i + 2 + atom_n]  # 读取坐标数据
                formatted_output_coordinate = [
                    [float(x.strip().split()[2]), float(x.strip().split()[3]), float(x.strip().split()[4])]
                    for x in output_coordinate
                ]
                step_data['coordinates'] = formatted_output_coordinate

                # 提取原子种类
                formatted_output_species = [x.strip().split()[1] for x in output_coordinate]
                step_data['species'] = formatted_output_species

            # **3. 读取 Step 信息**
            elif 'Step' in line:
                step_match = re.search(r"Step\s+(\d+)", line)
                if step_match:
                    step = int(step_match.group(1))
                    step_data['step'] = step  # 存储步骤

            # **4. 读取最大力（Max_Force）**
            elif " |  |F|max   |" in line:
                force_match = re.search(r"\|\s*\|F\|max\s*\|\s*(-?\d+\.\d+E?-?\d*)", line)
                if force_match:
                    force_str = force_match.group(1)
                    force_str = self.fix_scientific_notation(force_str)  # 处理科学计数法
                    try:
                        max_force_au = float(force_str)
                        step_data['force'] = max_force_au
                    except ValueError as e:
                        print(f"Error converting force value: {force_str} -> {e}")
                        step_data['force'] = None  # 转换失败设为 None

            # **存储当前步骤的数据，准备下一步**
            if step_data['force'] is not None and step_data['coordinates']:
                all_steps_data.append(step_data.copy())  # 存入数据
                step_data = {  # 重置数据字典
                    'energy': None,
                    'coordinates': [],
                    'species': [],
                    'step': None,
                    'force': None
                }

        return all_steps_data

    # 处理科学计数法格式，确保有效的浮点数
    def fix_scientific_notation(self, force_str):
        if 'E' in force_str:
            if force_str[-1] == 'E':  # 结尾是 'E'，加上默认的 '+00'
                force_str = force_str + '00'
            elif force_str[-2:] == 'E+':  # 结尾是 'E+'，加上默认的 '00'
                force_str = force_str + '00'
            elif force_str[-3:] == 'E-':  # 结尾是 'E-'，加上默认的 '00'
                force_str = force_str + '00'
        return force_str

if __name__ == '__main__':
    # 输入文件夹路径
    current_directory = input("请输入文件路径: ").strip()
    absolute_path = os.path.abspath(current_directory)
    folder_name = os.path.basename(absolute_path)

    if not os.path.isdir(current_directory):
        print("提供的路径无效，请检查路径并重新运行程序。")
        sys.exit(1)

    folder_prefix = 'dmol3'  # 目标文件夹前缀
    outdmol_paths = []  # 存储所有 .outmol 文件路径
    data = []

    # **遍历当前文件夹，获取所有 dmol3 文件夹内的 .outmol 文件**
    for root, dirs, files in os.walk(current_directory):
        if os.path.basename(root).startswith(folder_prefix):  # 以 dmol3 开头的文件夹
            file_path = os.path.join(root, "dmol.outmol")  # 获取 .outmol 文件路径
            if os.path.isfile(file_path):
                outdmol_paths.append(file_path)

    # **读取所有 .outmol 文件**
    with open(folder_name + '_paths.txt', 'w') as file:  
        for idx, path in enumerate(outdmol_paths, 0):
            abs_path = os.path.abspath(path)
            outdmol = read_outputdmol(path)
            # 显示当前读取的路径，且在同一行更新
            print(f"\r正在处理: {abs_path}", end='', flush=True)
            file.write(f"{idx} {abs_path}\n")  
            data.append(outdmol.Iron_step())  # 读取数据

    # **保存数据到 .npy 文件**
    data = np.array(data, dtype=object)                        
    np.save(folder_name + '.npy', data)
    print("\n处理完成！")  # 完成后输出
