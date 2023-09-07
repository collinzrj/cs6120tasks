import json, sys, uuid

def get_blocks(instrs):
    blocks = []
    block = []
    for inst in instrs:
        block.append(inst)
        if 'label' in inst.keys() or inst['op'] in ['jmp', 'br', 'call', 'ret']:
            blocks.append(block)
            block = []
    blocks.append(block)
    return blocks

## Global

def trivial_pass(instrs):
    used = set()
    for inst in instrs:
        if 'args' not in inst.keys():
            continue
        for arg in inst['args']:
            used.add(arg)
    new_block = []
    for inst in instrs:
        if 'label' in inst.keys() or inst['op'] in ['print', 'jmp', 'br', 'call', 'ret'] or 'dest' not in inst.keys() or inst['dest'] in used:
            new_block.append(inst)
    return new_block

def trivial_dce(instrs):
    while True:
        last_block_len = len(instrs)
        instrs = trivial_pass(instrs)
        new_block_len = len(instrs)
        if new_block_len == last_block_len:
            break
    return instrs

## Local
def lvn_opt(block):
    will_be_reversed = set()
    assigned_vars = set()
    for instr in reversed(block):
        if 'dest' in instr:
            if instr['dest'] in assigned_vars:
                will_be_reversed.add(json.dumps(instr))
            assigned_vars.add(instr['dest'])
    table = {}
    var2num = {}
    for instr in block:
        # skip lable
        if 'label' in instr:
            continue
        # don't optimize memory operations for now
        # if instr['op'] in ['alloc', 'free', 'store', 'load', 'ptradd']:
        #     continue
        if 'args' not in instr:
            continue
        num_args = []
        for arg in instr['args']:
            if arg in var2num:
                num_args.append(var2num[arg])
            else:
                num = len(table)
                var2num[arg] = num
                table[num] = (num, arg)
                num_args.append(arg)
        if 'dest' not in instr:
            if instr['op'] in ['print', 'return', 'store']:
                args = []
                for arg in instr['args']:
                    num = var2num[arg]
                    for entry in table.values():
                        if entry[0] == var2num[arg]:
                            args.append(entry[1])
                instr['args'] = args
            continue
        # make this a string
        # TODO: add sort function
        value = json.dumps((instr['op'], num_args))
        if value in table:
            num, var = table[value]
            instr['op'] = 'id'
            instr['args'] = [var]
        else:

            # TODO: optimize the code
            args = []
            for a in instr['args']:
                for entry in table.values():
                    if entry[0] == var2num[a]:
                        args.append(entry[1])
            if len(args) != len(instr['args']):
                print("ERROR!!!!!")
            instr['args'] = args

            num = len(table)
            dest = instr['dest']
            if json.dumps(instr) in will_be_reversed:
                var2num[dest] = num 
                dest = uuid.uuid4().hex
                instr['dest'] = dest
            else:
                dest = instr['dest']
            table[value] = (num, dest)
        
        var2num[instr['dest']] = num
    return block

def constant_fold_opt(block):
    constant_dict = {}
    new_block = []
    for instr in block:
        if 'op' not in instr:
            pass
        elif instr['op'] == 'const':
            constant_dict[instr['dest']] = instr['value']
        elif instr['op'] in ['add', 'mul', 'div', 'sub']:
            args = instr['args']
            op = instr['op']
            if set(args).issubset(constant_dict.keys()):
                if op == 'add':
                    result = constant_dict[args[0]] + constant_dict[args[1]] 
                elif op == 'mul':
                    result = constant_dict[args[0]] * constant_dict[args[1]] 
                elif op == 'div':
                    result = constant_dict[args[0]] / constant_dict[args[1]] 
                elif op == 'sub':
                    result = constant_dict[args[0]] - constant_dict[args[1]] 
                else:
                    print("Op should be in List!!!")
                instr = { "op": "const", "dest": instr['dest'], "type": instr['type'], "value": result }
                constant_dict[instr['dest']] = instr['value']
        new_block.append(instr)
    return new_block

def rename_opt(block):
    waiting_dict = {}
    remove_set = set()
    for idx, instr in enumerate(block):
        if 'args' in instr:
            for arg in instr['args']:
                if arg in waiting_dict:
                    waiting_dict.pop(arg)
        if 'dest' in instr:
            dest = instr['dest']
            if dest in waiting_dict:
                remove_set.add(waiting_dict[dest])
            waiting_dict[instr['dest']] = idx
    new_block = []
    for idx, instr in enumerate(block):
        if idx not in remove_set:
            new_block.append(instr)
    return new_block

def local_opt(fn, opts):
    new_blocks = []
    for block in get_blocks(fn['instrs']):
        for opt in opts:
            block = opt(block)
        new_blocks.append(block)
    instrs = []
    for block in new_blocks:
        for instr in block:
            instrs.append(instr)
    fn['instrs'] = instrs

def optimize_code(code):
    for fn in code['functions']:
        # local
        local_opt(fn, [lvn_opt, constant_fold_opt, rename_opt])
        # global
        fn['instrs'] = trivial_dce(fn['instrs'])
    return code

if __name__ == '__main__':
    if sys.argv[1] == 'brench':
        lines = ''
        while True:
            try:
                line = input()
                lines += line + '\n'
            except EOFError:
                break
        code = json.loads(lines)
        code = optimize_code(code)
        print(json.dumps(code, indent=2))
    else:
        file = sys.argv[2]
        with open(file, 'r') as f:
            code = json.load(f)
            code = optimize_code(code)
            print(json.dumps(code,  indent=2))