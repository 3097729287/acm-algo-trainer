from itertools import combinations_with_replacement


def check_a(inp, got, other):
    n = int(inp)
    values = list(map(int, got.split()))
    if values == [-1]:
        return other.strip() == '-1', '无解必须与独立枚举一致'
    if len(values) != 2 * n:
        return False, '需要两个长度为 n 的排列'
    a, b = values[:n], values[n:]
    if sorted(a) != list(range(1, n + 1)) or sorted(b) != list(range(1, n + 1)):
        return False, '每行必须是排列'
    # 小输入检查每个区间，大输入用所有长度 2 区间的必要充分条件。
    for row in (a, b):
        if n <= 9:
            for l in range(n):
                for r in range(l + 2, n + 1):
                    if max(row[l:r]) - min(row[l:r]) <= 1:
                        return False, '子区间极差不合法'
        elif any(abs(u - v) <= 1 for u, v in zip(row, row[1:])):
            return False, '相邻元素不合法'
    return all(abs(u - v) > 1 for u, v in zip(a, b)), '同列差必须大于 1'


def gen_a(rng):
    return str(rng.randint(1, 8)) + '\n'


def gen_c(rng):
    tests = [(rng.randint(1, 6), rng.randrange(8), rng.randrange(8), rng.randrange(8)) for _ in range(12)]
    return str(len(tests)) + '\n' + '\n'.join(' '.join(map(str, row)) for row in tests) + '\n'


def exhaustive_c():
    # 枚举数列本身，按实际与/或/异或建立最优值；不使用贪心结论。
    tests, expected = [], []
    for n in range(1, 7):
        best = {}
        for values in combinations_with_replacement(range(8), n):
            a, o, e, product = 7, 0, 0, 1
            for v in values:
                a &= v; o |= v; e ^= v; product *= v
            key = a, o, e
            best[key] = max(best.get(key, -1), product)
        for x in range(8):
            for y in range(8):
                for z in range(8):
                    tests.append(f'{n} {x} {y} {z}')
                    expected.append(str(best.get((x, y, z), -1)))
    return ('3 位数与六种长度的全部约束组合', str(len(tests)) + '\n' + '\n'.join(tests) + '\n', '\n'.join(expected))


def full_c():
    y = (1 << 60) - 1
    return '500000\n' + ''.join(f'{10**18-i%121} 0 {y} {i*1103515245 & y}\n' for i in range(500000))
