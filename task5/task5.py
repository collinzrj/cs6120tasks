import uuid, json, sys, graphviz
from copy import deepcopy


def build_cfg(fn_name, instrs):
    if len(instrs) == 0:
        return
    blocks = []
    ## give a unique name if no label
    current_block = []
    for inst in instrs:
        if 'label' in inst.keys():
            if len(current_block) > 0:
                blocks.append(current_block)
            current_block = [inst]
        elif inst['op'] in ['jmp', 'br', 'ret']:
            current_block.append(inst)
            if len(current_block) > 0:
                blocks.append(current_block)
            current_block = []
        else:
            current_block.append(inst)
    if len(current_block) > 0:
        blocks.append(current_block)
    # name the blocks
    name_block_list = []
    for block in blocks:
        if 'label' in block[0]:
            name_block_list.append((block[0]['label'], block))
        else:
            # insert a label if it doesn't have one
            new_label = f"label_{uuid.uuid4().hex[:4]}"
            block.insert(0, {"label": new_label})
            name_block_list.append((new_label, block))
    # print(fn_name, [x[0] for x in name_block_list])
    entry = name_block_list[0][0]
    # build the cfg
    block_children = {}
    for idx, (name, block) in enumerate(name_block_list):
        # print(fn_name, name, block)
        if 'op' in block[-1] and block[-1]['op'] in ['jmp', 'br', 'ret']:
            if 'labels' in block[-1]:
                # print(fn_name, name, block[-1]['labels'])
                block_children[name] = block[-1]['labels']
        else:
            # TODO: is this correct?
            # if it is not the last block
            if idx + 1 < len(name_block_list):
                block_children[name] = [name_block_list[idx + 1][0]]
    ## construct parents block
    block_parents = {}
    for (parent_name, children) in block_children.items():
        for child_name in children:
            block_parents.setdefault(child_name, []).append(parent_name)
    cfg = {}
    for (name, block) in name_block_list:
        if name not in block_parents:
            block_parents[name] = []
        if name not in block_children:
            block_children[name] = []
        cfg[name] = {}
        cfg[name]['parents'] = block_parents[name]
        cfg[name]['children'] = block_children[name]
        cfg[name]['content'] = block
    cfg_dot = graphviz.Digraph(comment=f'{fn_name}_cfg')
    for key in cfg.keys():
        cfg_dot.node(key)
    for key in cfg.keys():
        for child in cfg[key]['children']:
            cfg_dot.edge(key, child)
    cfg_dot.render(f'figs/{fn_name}_cfg.gv')
    # remove unaccessible block
    block_to_delete = []
    for block in cfg:
        if block == entry:
            continue
        if not has_path(cfg, entry, block, [], []):
            block_to_delete.append(block)
    for name in cfg:
        cfg[name]['parents'] = list(filter(lambda x : x not in block_to_delete, cfg[name]['parents']))
        cfg[name]['children'] = list(filter(lambda x : x not in block_to_delete, cfg[name]['children']))
    for block in block_to_delete:
        cfg.pop(block)
    return entry, cfg


def find_dominators(fn_name, instrs):
    """
    find the dominator of the nodes
    """
    # Find the dom of each vertex
    entry, cfg = build_cfg(fn_name, instrs)
    blocks = cfg.keys()
    dom_dict = {}
    for block in blocks:
        dom_dict[block] = set(blocks)
    dom_dict[entry] = {entry}
    prev_dom = {}
    while dom_dict != prev_dom:
        prev_dom = deepcopy(dom_dict)
        for block in blocks:
            current_res = dom_dict[block]
            for parent in cfg[block]['parents']:
                dom_dict.setdefault(parent, set())
                current_res = current_res.intersection(dom_dict[parent])
            current_res = {block}.union(current_res)
            dom_dict[block] = current_res
    return dom_dict, cfg, entry


def construct_imm_dominatee_dict(fn_name, dom_dict):
    """
    Construct the dominance tree
    """
    imm_dominatee_dict = {}
    # print("dom_dict", dom_dict)
    for block, dominators in dom_dict.items():
        # each of the dom of a block should be a dom of another dom, and the dom with the most dom except the current block should be the immediate dom
        dominators = sorted(dominators, key=lambda dominator: len(dom_dict[dominator]))
        if len(dominators) > 1:
            imm_dominatee_dict.setdefault(dominators[-2], []).append(block)
    return imm_dominatee_dict


def construct_dominance_tree(fn_name, dom_dict):
    """
    Construct the dominance tree
    """
    imm_dom_dict = {}
    for block, dominators in dom_dict.items():
        # each of the dom of a block should be a dom of another dom, and the dom with the most dom except the current block should be the immediate dom
        dominators = sorted(dominators, key=lambda dominator: len(dom_dict[dominator]))
        if len(dominators) > 1:
            imm_dom_dict[block] = dominators[-2]
    dom_dot = graphviz.Digraph(comment=f'{fn_name}_dom')
    for key in imm_dom_dict:
        dom_dot.node(key)
    for block, imm_dominator in imm_dom_dict.items():
        dom_dot.edge(imm_dominator, block)
    dom_dot.render(f'figs/{fn_name}_dom.gv')
    return dom_dot


def compute_dominance_frontier(fn_name, cfg, dom_dict):
    """
    Compute the dominance frontier
    """
    reverse_dom = {}
    for vertex, doms in dom_dict.items():
        for dom in doms:
            reverse_dom.setdefault(dom, set()).add(vertex)
    dom_frontier = {}
    for vertex, dominatees in reverse_dom.items():
        for dominatee in dominatees:
            # child of dominatee
            for grandchild in cfg[dominatee]['children']:
                # # should not be a direct dominatee of the vertex
                # if grandchild not in reverse_dom[vertex]:
                if grandchild not in reverse_dom[vertex] or vertex == grandchild:
                    dom_frontier.setdefault(vertex, set()).add(grandchild)
    # print(f'Dominance frontiers in {fn_name} is:')
    # for (k, v) in dom_frontier.items():
    #     print(k, v)
    # print("\n")
    return dom_frontier


def test_dom_dict(cfg, dom_dict, entry):
    blocks = cfg.keys()
    for dominatee in blocks:
        for dominator in blocks:
            # if in the dict, should be dominator, if not in the dict, should not be dominator
            if dominator in dom_dict[dominatee]:
                if not check_is_dom(cfg, dominator, dominatee, entry):
                    return False
            else:
                if check_is_dom(cfg, dominator, dominatee, entry):
                    return False
    return True


def check_is_dom(cfg, dominator, dominatee, entry):
    """
    if there exist a path from a to b but there doesn't exist a path from entry to b without visiting a,
    then a should be the dominator of b
    """
    if dominator == dominatee:
        return True
    if has_path(cfg, dominator, dominatee, [], []) and not has_path(cfg, entry, dominatee, [dominator], []):
        return True
    return False


def has_path(cfg, start, end, ignore_blocks, visited):
    # assume a block doesn't exist
    if start in ignore_blocks or start in visited:
        return False
    if end in cfg[start]['children']:
        return True
    for child in cfg[start]['children']:
        if has_path(cfg, child, end, ignore_blocks, visited + [start]):
            return True
    return False


if __name__ == '__main__':
    file = sys.argv[1]
    # file = '/Users/collin/Documents/Projects/cs6120tasks/task3/test/bitshift.json'
    with open(file, 'r') as f:
        code = json.load(f)
        for fn in code['functions']:
            fn_name = fn['name']
            dom_dict, cfg, entry = find_dominators(fn_name, fn['instrs'])
            if test_dom_dict(cfg, dom_dict, entry):
                print("test success!")
            else:
                print("test failed")
            dom_dot = construct_dominance_tree(fn_name, dom_dict)
            dom_frontier = compute_dominance_frontier(fn_name, cfg, dom_dict)