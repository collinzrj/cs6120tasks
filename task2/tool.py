# Here is a tool that removes the print operations in the code

import json, sys

def remove_print(file):
    with open(file, 'r') as f:
        code = json.load(f)
    for fn in code['functions']:
        fn['instrs'] = list(filter(lambda x: x['op'] != 'print', fn['instrs']))
    print(json.dumps(code,  indent=2))


if __name__ == '__main__':
    remove_print(sys.argv[1])