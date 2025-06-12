import os
import sys
import numpy as np
import re

# 更高精度的单位换算常数
HARTREE_TO_EV = 27.211386245988  # 1 Ha = 27.211386245988 eV
ROUND_DECIMALS = 8             # 保留小数位数，可根据需求调整

class read_outputdmol:
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
        """ 解析输出文件，提取计算数据，所有数值保留指定位数 """
        all_steps_data = []
        atom_n = self.atom_number()

        with open(self.outdmol_path) as f:
            lines = f.readlines()

        step_data = {
            'energy (eV)': None,
            'coordinates (au)': [],
            'species': [],
            'step': None,
            'max force (au)': None,
            'forces (au)': []
        }

        for i, line in enumerate(lines):
            # 1. 读取 SCF 总能量
            if 'Total Energy           Binding E       Cnvgnce     Time   Iter' in line:
                for j in range(i + 1, len(lines)):
                    if 'Message: SCF converged' in lines[j]:
                        val = lines[j - 1].split()[1]
                        if val.endswith('Ha'):
                            energy_ha = float(val[:-2])
                            energy_eV = energy_ha * HARTREE_TO_EV
                            step_data['energy (eV)'] = round(energy_eV, ROUND_DECIMALS)
                        break
                    if 'Error: SCF iterations not converged' in lines[j]:
                        return all_steps_data

            # 2. 读取原子坐标 + 读取力
            elif 'df              ATOMIC  COORDINATES (au)' in line:
                block = lines[i + 2 : i + 2 + atom_n]
                coords, species, forces = [], [], []
                for x in block:
                    x = self.fix_broken_numbers(x)
                    parts = x.strip().split()
                    if len(parts) == 8:
                        _, atom, xau, yau, zau, fx, fy, fz = parts
                        species.append(atom)
                        coords.append([
                            round(float(xau), ROUND_DECIMALS),
                            round(float(yau), ROUND_DECIMALS),
                            round(float(zau), ROUND_DECIMALS)
                        ])
                        forces.append([
                            round(float(fx), ROUND_DECIMALS),
                            round(float(fy), ROUND_DECIMALS),
                            round(float(fz), ROUND_DECIMALS)
                        ])
                step_data['coordinates (au)'] = coords
                step_data['species'] = species
                step_data['forces (au)'] = forces

            # 3. 读取 Step 信息
            elif 'Step' in line:
                m = re.search(r"Step\s+(\d+)", line)
                if m:
                    step_data['step'] = int(m.group(1))

            # 4. 读取最大力
            elif '|  |F|max   |' in line:
                m = re.search(r"\|\s*\|F\|max\s*\|\s*(-?\d+\.\d+E?[+-]?\d*)", line)
                if m:
                    fs = self.fix_scientific_notation(m.group(1))
                    try:
                        max_f = float(fs)
                        step_data['max force (au)'] = round(max_f, ROUND_DECIMALS)
                    except ValueError:
                        step_data['max force (au)'] = None

            # 存储数据
            if step_data['coordinates (au)'] and step_data['max force (au)'] is not None:
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

    def fix_broken_numbers(self, line: str) -> str:
        """ 修复数值拼接错误，例如 '68.559875-107.243239' """
        return re.sub(r'(\d)\s*([-+])\s*(\d)', r'\1 \2\3', line)

    def fix_scientific_notation(self, s: str) -> str:
        """ 处理科学计数法格式 """
        if 'E' in s and (s.endswith('E') or s.endswith('E+') or s.endswith('E-')):
            s += '00'
        return s


if __name__ == '__main__':
    current_directory = input('请输入文件路径: ').strip()
    if not os.path.isdir(current_directory):
        print('提供的路径无效，请检查路径并重新运行程序。')
        sys.exit(1)

    folder_name = os.path.basename(os.path.abspath(current_directory))
    outdmol_paths = []
    for root, dirs, files in os.walk(current_directory):
        for fname in files:
            if fname.lower().endswith('.outmol'):
                outdmol_paths.append(os.path.join(root, fname))

    with open(folder_name + '_paths.txt', 'w') as f:
        for idx, p in enumerate(outdmol_paths):
            f.write(f"{idx} {p}\n")

    data = []
    for path in outdmol_paths:
        print(f"正在处理: {path}")
        reader = read_outputdmol(path)
        steps = reader.Iron_step()
        print(f" → 解析到 {len(steps)} 步数据")
        data.append(steps)

    np.save(folder_name + '.npy', np.array(data, dtype=object))
    print('处理完成，保存至', folder_name + '.npy')
