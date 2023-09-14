"""dataflow analysis"""

import uuid, json, sys
from typing import Dict, Any, List

def build_cfg(instrs):
    """build cfg for global analysis in a function"""
    blocks = {}
    block_parents = {}
    block_children = {}
    ## give a unique name if no label
    name_block = (uuid.uuid4().hex, [])
    for inst in instrs:
        if 'label' in inst.keys():
            if len(name_block[1]) > 0:
                blocks[name_block[0]] = name_block[1]
            # TODO: check this
            last_block_name = name_block[0]
            name_block = (inst['label'], [inst])
            block_children.setdefault(last_block_name, set()).add(name_block[0])
        elif inst['op'] in ['jmp', 'br', 'call', 'ret']:
            name_block[1].append(inst)
            blocks[name_block[0]] = name_block[1]
            if 'labels' in inst:
                block_children.setdefault(name_block[0], set()).union(set(inst['labels']))
            last_block_name = name_block[0]
            name_block = (uuid.uuid4().hex, [])
            block_children.setdefault(last_block_name, set()).add(name_block[0])
        else:
            name_block[1].append(inst)
    ## append last block
    blocks[name_block[0]] = name_block[1]
    ## construct parents block
    for (parent_name, children) in block_children.items():
        for child_name in children:
            if child_name in block_parents:
                block_parents[child_name].append(parent_name)
            else:
                block_parents[child_name] = [parent_name]
    cfg = {}
    for (name, instrs) in blocks.items():
        if name not in block_parents:
            block_parents[name] = []
        if name not in block_children:
            block_children[name] = []
        cfg[name] = {}
        cfg[name]['parents'] = block_parents[name]
        cfg[name]['children'] = block_children[name]
        cfg[name]['content'] = instrs
    return cfg


class ReachabilityAnalyzer:
    """Analyzer that performs reachability analysis"""
    def __init__(self) -> None:
        # dictionary of dictionary
        # block label, var name, definitions
        self.block_in_dict: Dict[str, Dict[str, List]] = {}
        self.block_out_dict: Dict[str, Dict[str, List]] = {}

    def merge(self, labels):
        """merge function"""
        current_block_out: Dict[str, List] = {}
        for label in labels:
            if label not in self.block_out_dict:
                self.block_out_dict[label] = {}
            for (var, definitions) in self.block_out_dict[label].items():
                if var not in current_block_out:
                    current_block_out[var] = []
                current_block_out[var] += definitions
        return current_block_out

    def transfer(self, block, block_in):
        """transfer function"""
        for instr in block:
            if 'dest' in instr:
                # block_in[instr['dest']] = [instr]
                block_in[instr['dest']] = ['placeholder']
        return block_in


# TODO: check if this is correct
def worklist_algo(cfg, analyzer: ReachabilityAnalyzer):
    """worklist algorithm"""
    worklist: List[str] = list(cfg.keys())
    n = 0
    while len(worklist) > 1:
        n += 1
        if n > 100:
            break
        print(worklist)
        b = worklist.pop()
        analyzer.block_in_dict[b] = analyzer.merge(cfg[b]['parents'])
        if b not in analyzer.block_out_dict:
            analyzer.block_out_dict[b] = {}
        old_block_out_dict = analyzer.block_out_dict[b]
        analyzer.block_out_dict[b] = analyzer.transfer(cfg[b]['content'], analyzer.block_in_dict[b].copy())
        if analyzer.block_out_dict[b] != old_block_out_dict:
            worklist.extend(cfg[b]['children'])


def dataflow_analysis(fn):
    """entry point for dataflow analysis"""
    cfg = build_cfg(fn['instrs'])
    print("before cfg")
    for key in cfg:
        print(key, cfg[key])
    print("after cfg")
    analyzer = ReachabilityAnalyzer()
    worklist_algo(cfg, analyzer)
    return analyzer.block_in_dict, analyzer.block_out_dict

if __name__ == '__main__':
    file = '/Users/collin/Documents/Projects/cs6120tasks/task3/test/rect.json'
    # file = sys.argv[1]
    with open(file, 'r') as f:
        code = json.load(f)
        for fn in code['functions']:
            output = dataflow_analysis(fn)
            print("will print json")
            print(json.dumps(output, indent=2))

