"""dataflow analysis"""

import uuid, json, sys
from typing import Dict, Any, List


def build_cfg(instrs):
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
            name_block_list.append((uuid.uuid4().hex, block))
    # build the cfg
    block_children = {}
    for idx, (name, block) in enumerate(name_block_list):
        if 'op' in block[-1] and block[-1]['op'] in ['jmp', 'br', 'ret']:
            if 'labels' in block[-1]:
                block_children[name] = block[-1]['labels']
        else:
            # TODO: is this correct?
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
    # for (key, val) in cfg.items():
    #     print(key, val)
    return cfg

class ReachabilityAnalyzer:
    """Analyzer that performs reachability analysis"""
    def __init__(self) -> None:
        # dictionary of dictionary
        # block label, var name, definitions
        self.block_in_dict: Dict[str, Dict[str, List]] = {}
        self.block_out_dict: Dict[str, Dict[str, List]] = {}
        self.definition_dict: Dict[str, Any] = {}

    def merge(self, labels):
        """merge function"""
        current_block_out: Dict[str, List] = {}
        for label in labels:
            if label not in self.block_out_dict:
                self.block_out_dict[label] = {}
            for (var, definitions) in self.block_out_dict[label].items():
                current_block_out[var] = current_block_out.setdefault(var, set()).union(definitions)
        return current_block_out

    def transfer(self, block, block_in):
        """transfer function"""
        for instr in block:
            if 'dest' in instr:
                # block_in[instr['dest']] = [instr]
                definition_id = uuid.uuid4().hex
                self.definition_dict[definition_id] = instr
                block_in[instr['dest']] = {definition_id}
        return block_in


# TODO: check if this is correct
def worklist_algo(cfg, analyzer: ReachabilityAnalyzer):
    """worklist algorithm"""
    worklist = set(cfg.keys())
    while len(worklist) > 0:
        print(worklist)
        b = worklist.pop()
        analyzer.block_in_dict[b] = analyzer.merge(cfg[b]['parents'])
        old_block_out_dict = analyzer.block_out_dict.setdefault(b, {})
        analyzer.block_out_dict[b] = analyzer.transfer(cfg[b]['content'], analyzer.block_in_dict[b].copy())
        if analyzer.block_out_dict[b] != old_block_out_dict:
            worklist.union(cfg[b]['children'])


def dataflow_analysis(fn):
    """entry point for dataflow analysis"""
    cfg = build_cfg(fn['instrs'])
    analyzer = ReachabilityAnalyzer()
    worklist_algo(cfg, analyzer)
    block_in_dict = analyzer.block_in_dict
    for label in block_in_dict:
        for var in block_in_dict[label]:
            block_in_dict[label][var] = [analyzer.definition_dict[definition] for definition in block_in_dict[label][var]]
    block_out_dict = analyzer.block_out_dict
    for label in block_out_dict:
        for var in block_out_dict[label]:
            block_out_dict[label][var] = [analyzer.definition_dict[definition] for definition in block_out_dict[label][var]]
    return block_in_dict, block_out_dict

if __name__ == '__main__':
    file = sys.argv[1]
    with open(file, 'r') as f:
        code = json.load(f)
        for fn in code['functions']:
            output = dataflow_analysis(fn)
            print("####INPUT####")
            print(output[0])
            print("####OUTPUT####")
            print(output[1])
