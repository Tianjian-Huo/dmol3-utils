import os
import sys
import numpy as np
import re

class read_outputdmol():
    def __init__(self, outdmol_path: str) -> None:
        self.outdmol_path = outdmol_path  # 输出文件路径

    def atom_number(self) -> int:
        """ 获取原子数量 """
        with open(self.outdmol_path) as f:
            for line in f:
                if 'N_atoms =' in line:
                    return int(line.split()[2])
        return None

    def Iron_step(self) -> list:
        """ 解析输出文件，提取计算数据 """
        all_steps_data = []  
        atom_n = self.atom_number()  # 获取原子数量

        with open(self.outdmol_path) as f:
            lines = f.readlines()

        step_data = {
            'energy (eV)': None,
            'coordinates (au)': [],
            'species': [],
            'step': None,
            'max force (au)': None,
            'forces (au)': []  # 存储所有原子的力
        }

        for i, line in enumerate(lines):
            # **1. 读取 SCF 总能量**
            if 'Total Energy           Binding E       Cnvgnce     Time   Iter' in line:
                for j in range(i + 1, len(lines)):
                    energy_line = lines[j].strip()
                    if 'Message: SCF converged' in energy_line:
                        energy_value = lines[j - 1].split()[1]  
                        if energy_value.endswith("Ha"):
                            energy_value_eV = float(energy_value[:-2]) * 27.212  
                            step_data['energy (eV)'] = energy_value_eV
                        break
                    elif 'Error: SCF iterations not converged' in energy_line:
                        return all_steps_data  

            # **2. 读取原子坐标 + 读取力**
            elif "df              ATOMIC  COORDINATES (au)" in line:
                output_coordinate = lines[i + 2:i + 2 + atom_n]  
                formatted_output_coordinate = [
                    [float(x.strip().split()[2]), float(x.strip().split()[3]), float(x.strip().split()[4])]
                    for x in output_coordinate
                ]
                step_data['coordinates (au)'] = formatted_output_coordinate

                formatted_output_species = [x.strip().split()[1] for x in output_coordinate]
                step_data['species'] = formatted_output_species

                # **同时读取三方向的力**
                formatted_output_forces = [
                    [float(x.strip().split()[5]), float(x.strip().split()[6]), float(x.strip().split()[7])]
                    for x in output_coordinate
                ]
                step_data['forces (au)'] = formatted_output_forces  

            # **3. 读取 Step 信息**
            elif 'Step' in line:
                step_match = re.search(r"Step\s+(\d+)", line)
                if step_match:
                    step = int(step_match.group(1))
                    step_data['step'] = step  

            # **4. 读取最大力**
            elif " |  |F|max   |" in line:
                force_match = re.search(r"\|\s*\|F\|max\s*\|\s*(-?\d+\.\d+E?-?\d*)", line)
                if force_match:
                    force_str = force_match.group(1)
                    force_str = self.fix_scientific_notation(force_str)  
                    try:
                        max_force_au = float(force_str)
                        step_data['max force (au)'] = max_force_au
                    except ValueError as e:
                        print(f"Error converting force value: {force_str} -> {e}")
                        step_data['max force (au)'] = None  

            # **存储数据**
            if step_data['max force (au)'] is not None and step_data['coordinates (au)']:
                all_steps_data.append(step_data.copy())  
                step_data = {  
                    'energy (eV)': None,
                    'coordinates (au)': [],
                    'species': [],
                    'step': None,
                    'max force (au)': None,
                    'forces (au)': []  
                }

        return all_steps_data

    def fix_scientific_notation(self, force_str):
        """ 处理科学计数法格式 """
        if 'E' in force_str:
            if force_str[-1] == 'E':  
                force_str = force_str + '00'
            elif force_str[-2:] == 'E+':  
                force_str = force_str + '00'
            elif force_str[-3:] == 'E-':  
                force_str = force_str + '00'
        return force_str

if __name__ == '__main__':
    current_directory = input("请输入文件路径: ").strip()
    absolute_path = os.path.abspath(current_directory)
    folder_name = os.path.basename(absolute_path)

    if not os.path.isdir(current_directory):
        print("提供的路径无效，请检查路径并重新运行程序。")
        sys.exit(1)

    folder_prefix = 'dmol3'  
    outdmol_paths = []  
    data = []

    for root, dirs, files in os.walk(current_directory):
        if os.path.basename(root).startswith(folder_prefix):  
            file_path = os.path.join(root, "dmol.outmol")  
            if os.path.isfile(file_path):
                outdmol_paths.append(file_path)

    with open(folder_name + '_paths.txt', 'w') as file:  
        for idx, path in enumerate(outdmol_paths, 0):
            abs_path = os.path.abspath(path)
            outdmol = read_outputdmol(path)
            print(f"\r正在处理: {abs_path}", end='', flush=True)
            file.write(f"{idx} {abs_path}\n")  
            data.append(outdmol.Iron_step())  

    data = np.array(data, dtype=object)                        
    np.save(folder_name + '.npy', data)
    print("\n处理完成！")
