import os
import sys
import re
import numpy as np

ROUND_DECIMALS = 8  # 保留小数位数

def clean_num(x: float) -> float:
    """
    先格式化到 ROUND_DECIMALS 位小数，
    再去掉末尾多余的 '0' 和小数点，
    转回 float 以让 Python repr 自动省略不必要的 0。
    """
    s = f"{x:.{ROUND_DECIMALS}f}".rstrip('0').rstrip('.')
    return float(s)

class read_outputdmol:
    def __init__(self, outdmol_path: str) -> None:
        self.outdmol_path = outdmol_path

    def atom_number(self) -> int:
        with open(self.outdmol_path) as f:
            for line in f:
                if 'N_atoms =' in line:
                    return int(line.split()[2])
        return 0

    def fix_broken_numbers(self, line: str) -> str:
        return re.sub(r'(\d)\s*([-+])\s*(\d)', r'\1 \2\3', line)

    def fix_scientific_notation(self, s: str) -> str:
        if 'E' in s and (s.endswith('E') or s.endswith('E+') or s.endswith('E-')):
            s += '00'
        return s

    def Iron_step(self) -> list:
        all_steps = []
        atom_n = self.atom_number()

        with open(self.outdmol_path) as f:
            lines = f.readlines()

        # 每步数据模板，含 orb (eV)
        step_data = {
            'energy (Ha)':    None,
            'coordinates (au)': [],
            'species':         [],
            'step':            None,
            'max force (au)':  None,
            'forces (au)':     [],
            'orb (eV)':        []
        }

        i = 0
        while i < len(lines):
            L = lines[i]

            # 1. SCF 总能量 (Ha)
            if 'Total Energy           Binding E       Cnvgnce     Time   Iter' in L:
                for j in range(i+1, len(lines)):
                    t = lines[j].strip()
                    if 'Message: SCF converged' in t:
                        val = lines[j-1].split()[1]
                        if val.endswith('Ha'):
                            e_ha = float(val[:-2])
                            step_data['energy (Ha)'] = clean_num(e_ha)
                        break
                    if 'Error: SCF iterations not converged' in t:
                        return all_steps

            # 2. 轨道能级
            elif L.strip().startswith('state') and 'eigenvalue' in L and 'occupation' in L:
                orb_list = []
                # 跳到数据行：跳过表头(i)、单位行(i+1)、空行(i+2)
                j = i + 3
                # 只要行以数字开头就继续读
                while j < len(lines) and re.match(r'\s*\d+', lines[j]):
                    parts = lines[j].split()
                    if len(parts) >= 7:
                        state_str = ' '.join(parts[0:4])
                        ev_ev     = clean_num(float(parts[5]))
                        occ       = clean_num(float(parts[6]))
                        orb_list.append((state_str, ev_ev, occ))
                    j += 1
                step_data['orb (eV)'] = orb_list
                i = j
                continue

            # 3. 原子坐标 + 力
            elif 'df              ATOMIC  COORDINATES (au)' in L:
                block = lines[i+2 : i+2+atom_n]
                coords, sp, fs = [], [], []
                for row in block:
                    row = self.fix_broken_numbers(row)
                    p = row.strip().split()
                    if len(p) == 8:
                        _, atom, xau, yau, zau, fx, fy, fz = p
                        sp.append(atom)
                        coords.append([
                            clean_num(float(xau)),
                            clean_num(float(yau)),
                            clean_num(float(zau))
                        ])
                        fs.append([
                            clean_num(float(fx)),
                            clean_num(float(fy)),
                            clean_num(float(fz))
                        ])
                step_data['coordinates (au)'] = coords
                step_data['species']         = sp
                step_data['forces (au)']     = fs

            # 4. 步数编号
            elif 'Step' in L:
                m = re.search(r"Step\s+(\d+)", L)
                if m:
                    step_data['step'] = int(m.group(1))

            # 5. 最大力
            elif '|  |F|max   |' in L:
                m = re.search(r"\|\s*\|F\|max\s*\|\s*(-?\d+\.\d+E?[+-]?\d*)", L)
                if m:
                    num = self.fix_scientific_notation(m.group(1))
                    try:
                        step_data['max force (au)'] = clean_num(float(num))
                    except ValueError:
                        step_data['max force (au)'] = None

            # 存储并重置，保留 orb (eV)
            if step_data['coordinates (au)'] and step_data['max force (au)'] is not None:
                all_steps.append(step_data.copy())
                step_data = {
                    'energy (Ha)':    None,
                    'coordinates (au)': [],
                    'species':         [],
                    'step':            None,
                    'max force (au)':  None,
                    'forces (au)':     [],
                    'orb (eV)':        step_data['orb (eV)']
                }

            i += 1

        return all_steps


if __name__ == '__main__':
    current_directory = input('请输入文件路径: ').strip()
    if not os.path.isdir(current_directory):
        print('提供的路径无效，请检查后重试。')
        sys.exit(1)

    folder = os.path.basename(os.path.abspath(current_directory))
    paths = []
    for root, _, files in os.walk(current_directory):
        for fn in files:
            if fn.lower().endswith('.outmol'):
                paths.append(os.path.join(root, fn))

    with open(f'{folder}_paths.txt', 'w') as f:
        for idx, p in enumerate(paths):
            f.write(f'{idx} {p}\n')

    all_data = []
    for p in paths:
        print(f'Processing {p} ...', end='')
        reader = read_outputdmol(p)
        steps = reader.Iron_step()
        print(f' parsed {len(steps)} steps')
        all_data.append(steps)

    np.save(f'{folder}.npy', np.array(all_data, dtype=object))
    print('Done. Saved to', f'{folder}.npy')
