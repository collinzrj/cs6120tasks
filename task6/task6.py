import uuid, json, sys, graphviz, copy
sys.path.append('../')
from task5.task5 import build_cfg, find_dominators, compute_dominance_frontier, construct_imm_dominatee_dict, test_dom_dict
from task3.optimization import trivial_dce

SHOULD_TEST = False

def myprint(x):
    if SHOULD_TEST:
        print(x)


def construct_var_block_dict(cfg):
    var_block_dict = {}
    for block in cfg.keys():
        for instr in cfg[block]['content']:
            if 'dest' in instr:
                # type might be a dict
                var_type = json.dumps(instr['type'])
                var_block_dict.setdefault(instr['dest'], set()).add((block, var_type))
    return var_block_dict


def insert_phi_nodes(var_block_dict, dom_frontier, cfg):
    # Insert phi nodes
    for var, definition_blocks in var_block_dict.items():
        while len(definition_blocks) > 0:
            (df_block, var_type) = definition_blocks.pop()
            var_type = json.loads(var_type)
            if df_block in dom_frontier:
                for frontier in dom_frontier[df_block]:
                    cfg[frontier].setdefault('phi_nodes', {})
                    if var not in cfg[frontier]['phi_nodes']:
                        num_parents = len(cfg[frontier]['parents'])
                        phi_node = {
                            "original_dest": var,
                            "dest": var,
                            "type": var_type,
                            "op": "phi",
                            "args": [],
                            "labels": []
                        }
                        cfg[frontier]['phi_nodes'][var] = phi_node
                        # TODO: is this correct? check this for bug
                        definition_blocks.add((frontier, json.dumps(var_type)))
    return cfg


def rename(block, cfg, stack, imm_dom_dict):
    myprint(f"renaming block {block}")
    new_content = []
    # rename phi node dest
    for phi_node in cfg[block].setdefault('phi_nodes', {}).values():
        stack.setdefault(phi_node['dest'], [])
        new_dest = f"{phi_node['dest']}_{uuid.uuid4().hex[:8]}"
        stack[phi_node['dest']].append(new_dest)
        phi_node['dest'] = new_dest
    for instr in cfg[block]['content']:
        # print(instr)
        new_instr = instr.copy()
        if 'args' in instr:
            new_args = []
            for arg in instr['args']:
                if arg in stack:
                    new_args.append(stack[arg][-1])
                else:
                    new_args.append(arg)
            new_instr['args'] = new_args
            # print('tttt', block, new_args, stack)
        if 'dest' in instr:
            myprint(f"rename {instr}")
            stack.setdefault(instr['dest'], [])
            new_instr['dest'] = f"{instr['dest']}_{uuid.uuid4().hex[:8]}"
            stack[instr['dest']].append(new_instr['dest'])
        new_content.append(new_instr)
    cfg[block]['content'] = new_content
    for child in cfg[block]['children']:
        for phi_node in cfg[child].setdefault('phi_nodes', {}).values():
            if phi_node['original_dest'] in stack:
                arg = stack[phi_node['original_dest']][-1]
            else:
                arg = "__undefined"
            phi_node['labels'].append(block)
            phi_node['args'].append(arg)
    for imm_dominatee in imm_dom_dict.setdefault(block, []):
        rename(imm_dominatee, cfg, copy.deepcopy(stack), imm_dom_dict)


def construct_function_from_cfg(cfg):
    new_fn = []
    for key in cfg:
        content = cfg[key]['content']
        if 'phi_nodes' in cfg[key]:
            if 'label' not in content[0]:
                print("first instr must be label!")
            content = content[:1] + list(cfg[key]['phi_nodes'].values()) + content[1:]
        new_fn += content
    return new_fn


def to_ssa(code):
    for fn in code['functions']:
        fn_name = fn['name']
        dom_dict, cfg, entry = find_dominators(fn_name, fn['instrs'])
        myprint(f"test dom dict {test_dom_dict(cfg, dom_dict, entry)}")
        var_block_dict = construct_var_block_dict(cfg)
        dom_frontier = compute_dominance_frontier(fn_name, cfg, dom_dict)
        cfg = insert_phi_nodes(var_block_dict, dom_frontier, cfg)
        imm_dom_dict = construct_imm_dominatee_dict(fn_name, dom_dict)
        myprint(f"dom dict {dom_dict}")
        myprint(f"imm dom {imm_dom_dict}")
        # initialize the stack
        stack = {}
        if 'args' in fn:
            for arg in fn['args']:
                name = arg['name']
                stack[name] = [name]
        rename(entry, cfg, stack, imm_dom_dict)
        new_fn = construct_function_from_cfg(cfg)
        instrs = []
        defined_vars = []
        for instr in new_fn:
            if 'args' in instr:
                if '__undefined' in instr['args']:
                    continue
            if 'dest' in instr:
                defined_vars.append(instr['dest'])
            instrs.append(instr)
        new_fn = trivial_dce(instrs)
        fn['instrs'] = new_fn
    return code


def from_ssa(code):
    for fn in code['functions']:
        entry, cfg = build_cfg(fn['name'], fn['instrs'])
        for block in cfg:
            new_content = []
            for instr in cfg[block]['content']:
                if 'op' in instr and instr['op'] == 'phi':
                    for idx in range(len(instr['args'])):
                        parent = instr['labels'][idx]
                        arg = instr['args'][idx]
                        # has control flow at the end
                        new_instr = {
                                "op": "id",
                                "dest": instr['dest'],
                                "type": instr['type'],
                                "args": [ arg ]
                            }
                        if len(cfg[parent]['content']) > 1 and 'op' in cfg[parent]['content'][-1] and cfg[parent]['content'][-1]['op'] in ['jmp', 'br', 'ret']:
                            cfg[parent]['content'].insert(len(cfg[parent]['content']) - 1, new_instr)
                        else:
                            cfg[parent]['content'].append(new_instr)
                else:
                    new_content.append(instr)
            cfg[block]['content'] = new_content
        new_fn = construct_function_from_cfg(cfg)
        fn['instrs'] = new_fn
    return code



if __name__ == '__main__':
    # file = sys.argv[1]
    # with open(file, 'r') as f:
    #     code = json.load(f)
    lines = ''
    while True:
        try:
            line = input()
            lines += line + '\n'
        except EOFError:
            break
    code = json.loads(lines)
    new_code = to_ssa(code)
    new_code = from_ssa(new_code)
    print(json.dumps(new_code, indent=2))
