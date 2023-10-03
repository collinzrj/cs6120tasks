if __name__ == '__main__':
    result = {}
    with open('to_ssa.output') as f:
        lines = f.readlines()
        grouped_lines = [lines[i:i + 4] for i in range(0, len(lines), 4)]
        for group in grouped_lines:
            name = group[0].strip('\n').split('/')[-1]
            original_result = group[1].strip('\n').split(' ')[-1]
            new_result = group[2].strip('\n').split(' ')[-1]
            result[name] = {'original': original_result, 'to_ssa': new_result}
            print(name, original_result, new_result)
    with open('from_ssa.output') as f:
        lines = f.readlines()
        grouped_lines = [lines[i:i + 4] for i in range(0, len(lines), 4)]
        for group in grouped_lines:
            name = group[0].strip('\n').split('/')[-1]
            original_result = group[1].strip('\n').split(' ')[-1]
            new_result = group[2].strip('\n').split(' ')[-1]
            result[name]['to_and_from_ssa'] = new_result
    print("| name | original | to_ssa | to_and_from_ssa |")
    print("| ----- | ----- | ----- | ----- |")
    for name, dict in result.items():
        dict.setdefault('to_and_from_ssa', 'missed')
        line = ' | '.join([name, dict['original'], dict['to_ssa'], dict['to_and_from_ssa']])
        line = f"| {line} |"
        print(line)