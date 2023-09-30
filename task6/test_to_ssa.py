import os
import glob


root_dir = '/Users/collin/Documents/Projects/bril/benchmarks'
extension = '.bril'
file_list = glob.glob(os.path.join(root_dir, '**', f'*{extension}'), recursive=True)

for file_path in file_list:
    # os.system(f"python3 task6.py {file_path} | python3 is_ssa.py")
    print(file_path)
    # os.system(f"/Users/collin/Library/Python/3.11/bin/bril2json < {file_path} | python3 task6.py")
    os.system(f"/Users/collin/Library/Python/3.11/bin/bril2json < {file_path} | python3 task6.py | python3 is_ssa.py")