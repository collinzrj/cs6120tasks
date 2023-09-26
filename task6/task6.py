import uuid, json, sys, graphviz, copy
sys.path.append('../')
from task5.task5 import build_cfg, find_dominators, compute_dominance_frontier, construct_imm_dominatee_dict


def construct_var_block_dict(cfg):
    var_block_dict = {}
    for block in cfg.keys():
        for instr in cfg[block]['content']:
            if 'dest' in instr:
                var_block_dict.setdefault(instr['dest'], set()).add(block)
    return var_block_dict


def insert_phi_nodes(var_block_dict, dom_frontier, cfg):
    # Insert phi nodes
    for var, definition_blocks in var_block_dict.items():
        while len(definition_blocks) > 0:
            df_block = definition_blocks.pop()
            if df_block in dom_frontier:
                for frontier in dom_frontier[df_block]:
                    cfg[frontier].setdefault('phi_nodes', {})
                    if var not in cfg[frontier]['phi_nodes']:
                        num_parents = len(cfg[frontier]['parents'])
                        phi_node = {
                            "var": var,
                            "op": "phi",
                            "args": [],
                            "labels": []
                        }
                        cfg[frontier]['phi_nodes'][var] = phi_node
                        # TODO: is this correct? check this for bug
                        definition_blocks.add(df_block)
    return cfg


def rename(block, cfg, stack, imm_dom_dict):
    print(f"renaming {block} {stack}")
    new_content = []
    for instr in cfg[block]['content']:
        new_instr = instr.copy()
        if 'args' in instr:
            new_args = []
            for arg in instr['args']:
                if arg in stack:
                    new_args.append(stack[arg][-1])
                else:
                    print(f"Error! arg {arg} should be in stack")
            new_instr['args'] = new_args
            # print('tttt', block, new_args, stack)
        if 'dest' in instr:
            stack.setdefault(instr['dest'], [])
            new_instr['dest'] = f"{instr['dest']}_{uuid.uuid4().hex[:8]}"
            stack[instr['dest']].append(new_instr['dest'])
        new_content.append(new_instr)
    cfg[block]['content'] = new_content
    for child in cfg[block]['children']:
        for phi_node in cfg[child].setdefault('phi_nodes', {}).values():
            print('phi_node', phi_node)
            phi_node['labels'].append(block)
            phi_node['args'].append(stack[phi_node['var']][-1])
    for imm_dominatee in imm_dom_dict.setdefault(block, []):
        print(f"{block} call rename", stack)
        rename(imm_dominatee, cfg, copy.deepcopy(stack), imm_dom_dict)
        print(f"{block} call rename finish", stack)



if __name__ == '__main__':
    # file = sys.argv[1]
    file = '/Users/collin/Documents/Projects/cs6120tasks/task3/test/simple_branch.json'
    with open(file, 'r') as f:
        code = json.load(f)
    for fn in code['functions']:
        fn_name = fn['name']
        dom_dict, cfg, entry = find_dominators(fn_name, fn['instrs'])
        var_block_dict = construct_var_block_dict(cfg)
        dom_frontier = compute_dominance_frontier(fn_name, cfg, dom_dict)
        cfg = insert_phi_nodes(var_block_dict, dom_frontier, cfg)
        imm_dom_dict = construct_imm_dominatee_dict(fn_name, dom_dict)
        print('imm', imm_dom_dict)
        print('cfg', cfg)
        rename(entry, cfg, {}, imm_dom_dict)
        for k, v in cfg.items():
            print(k, v)