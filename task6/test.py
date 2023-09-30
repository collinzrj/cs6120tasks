import re, glob, os, subprocess


ARGS_RE = r'ARGS: (.*)'

if __name__ == '__main__':
    # Define the root directory
    root_dir = '/Users/collin/Documents/Projects/bril/benchmarks'

    # Define the file extension to search for
    extension = '.bril'

    # Use glob to find all files with the specified extension in subfolders
    file_list = glob.glob(os.path.join(root_dir, '**', f'*{extension}'), recursive=True)

    # Iterate through the list of files
    for file_path in file_list:
        with open(file_path, 'r') as f:
            try:
                content = f.read()
                match = re.search(ARGS_RE, content)
                args = match.group(1) if match else ''
                print(file_path)
                first_output = subprocess.check_output(f'/Users/collin/Library/Python/3.11/bin/bril2json < {file_path} | brilirs -p {args}', shell=True)
                second_output = subprocess.check_output(f'/Users/collin/Library/Python/3.11/bin/bril2json < {file_path} | python3 task6.py | brilirs -p {args}', shell=True, timeout=5)
                print(first_output == second_output)
            except Exception:
                print(file_path, "failed!")
            
/Users/collin/Documents/Projects/bril/benchmarks/core/perfect.bril

/Users/collin/Library/Python/3.11/bin/bril2json < /Users/collin/Documents/Projects/bril/benchmarks/core/perfect.bril | brilirs -p {args}