from pathlib import Path
import shutil

id_file = Path("instances.txt")
source_dir = Path("../../qplib/html/sol")
target_dir = Path("../data/sol")

target_dir.mkdir(exist_ok=True)

moved = 0
missing = []

with id_file.open() as f:
    for line in f:
        line = line.strip()
        if not line or line == 'END':
            continue

        id = line.split()[0]
        if id == 'name':
            continue

        file_path = source_dir / f"QPLIB_{id}.sol"

        if file_path.is_file():
            shutil.move(str(file_path), str(target_dir / file_path.name))
            moved += 1
        else:
            missing.append(line)

print(f"Moved {moved} files into {target_dir}/")

if missing:
    print(f"Could not find {len(missing)} files:")
    print(", ".join(missing))