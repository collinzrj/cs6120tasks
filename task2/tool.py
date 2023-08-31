# Here is a tool that removes the print operations in the code

import json, sys

def remove_print(file):
    with open(file, 'r') as f:
        code = json.load(f)
    for fn in code['functions']:
        fn['instrs'] = list(filter(lambda x: 'op' not in x or x['op'] != 'print', fn['instrs']))
    print(json.dumps(code,  indent=2))


if __name__ == '__main__':
    print(sys.argv[1])
    remove_print(sys.argv[1])