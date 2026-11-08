"""Exact teaching traces for forced columns, merge counting and window shrink."""
import json
import math

from nowcoder_animations import (ACTIVE, BLUE, DEAD, INK, MUTED, RED, SOFT, TEAL,
                                RECORDS, array, attach, box, canvas, save, text, wrap)


def forced_columns():
    original = [[int(c) for c in row] for row in ['0010', '0111', '1000', '1011']]
    n, m = 4, 4
    initial = [sum(original[r][c] << r for r in range(n)) for c in range(m)]
    presses = None
    for first in range(1 << n):
        previous, current, attempt = 0, first, []
        for c in range(m):
            attempt.append(current)
            following = initial[c] ^ previous ^ current ^ ((current << 1) & 15) ^ (current >> 1)
            previous, current = current, following
        if current == 0:
            presses = attempt
            break
    assert presses is not None
    board, used = [row[:] for row in original], [0] * m
    states = [([row[:] for row in board], used[:], -1, '从原题的四乘四样例出发，枚举首列的按法；这里展示其中一个成功方案。')]
    for c, mask in enumerate(presses):
        if c:
            assert mask == sum(board[r][c - 1] << r for r in range(n))
        marks = ''.join(str(mask >> r & 1) for r in range(n))
        note = (f'首列猜测：从上到下按键为 {marks}。' if c == 0 else
                f'第 {c} 列尚亮的位置，强迫第 {c + 1} 列在同一行按下；从上到下为 {marks}。')
        states.append(([row[:] for row in board], used[:], c, note))
        for r in range(n):
            if mask >> r & 1:
                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < n and 0 <= cc < m:
                        board[rr][cc] ^= 1
        used[c] = mask
        if c:
            assert all(board[r][j] == 0 for r in range(n) for j in range(c))
        states.append(([row[:] for row in board], used[:], c,
                       f'第 {c + 1} 列操作完成。它左边的所有列已经熄灭，后续不会再触碰。'))
    assert not any(map(any, board))
    assert states[0][0] == original
    states.append(([row[:] for row in board], used[:], m,
                   '最后一列也全部熄灭，虚拟的下一列不需要任何按键；当前首列猜测可行。'))
    frames = []
    for step, (grid, done, current, note) in enumerate(states):
        frame, draw = canvas('翻转游戏：首列一旦选定，后续逐列被强迫', step, len(states), note)
        for c in range(m):
            text(draw, (160 + 100 * c, 105), f'第{c + 1}列', 20, BLUE if c == current else MUTED, 'mm')
            for r in range(n):
                box(draw, (118 + c * 100, 130 + r * 65, 202 + c * 100, 185 + r * 65), grid[r][c],
                    fill=ACTIVE if grid[r][c] == 0 else '#f7ded4',
                    outline=BLUE if c == current else None)
        text(draw, (585, 132), '本列按键（上 → 下）', 22, MUTED)
        for c in range(m):
            bits = ''.join(str(done[c] >> r & 1) for r in range(n))
            text(draw, (590, 182 + c * 47), f'{c + 1} 列：{bits}', 23, BLUE if c == current else INK)
        frames.append(frame)
    save('flip-forced-columns', frames, [285342, 285340],
         '一表示灯亮，零表示灯灭；对首列的一个猜测逐列验证，上一列亮位唯一决定本列按键。',
         {'initialRows': original, 'pressMasksTopBitZero': presses, 'finalRows': board})


def merge_count():
    left, right = [4, 5], [1, 2, 3]
    i = j = 0
    output, count = [], 1
    states = [(i, j, output[:], count, '左右半段已分别排好序；右半段原来的 (3,2) 已贡献一对。')]
    while i < len(left) or j < len(right):
        if j == len(right) or i < len(left) and left[i] <= right[j]:
            value = left[i]
            i += 1
            note = (f'右半段已取完，把剩余左侧的 {value} 并入，不新增跨段逆序。' if j == len(right) else
                    f'取左边 {value}，它不大于右侧当前值，不产生新的跨段逆序。')
        else:
            value = right[j]
            count += len(left) - i
            j += 1
            note = f'取右边 {value}；左边尚有 {len(left) - i} 项都比它大，一次新增 {len(left) - i} 对。'
        output.append(value)
        states.append((i, j, output[:], count, note))
    assert count == 7 and output == [1, 2, 3, 4, 5]
    frames = []
    for step, (i, j, out, count, note) in enumerate(states):
        frame, draw = canvas('归并计数：右端胜出时，一次计算左侧剩余项', step, len(states), note)
        text(draw, (38, 105), '左半段', 23)
        array(draw, left, y=145, x=38, cell=110, active=[i], invalid=range(i))
        text(draw, (390, 105), '右半段', 23)
        array(draw, right, y=145, x=390, cell=110, active=[j], invalid=range(j))
        text(draw, (38, 240), '已合并', 23)
        array(draw, out, y=280, x=38, cell=110)
        text(draw, (38, 383), f'逆序对累计：{count}', 28, TEAL)
        frames.append(frame)
    save('inversion-merge', frames, [15163],
         '原例为 4、5、1、3、2；先算子段内部的一对，再在跨段合并中新增六对，总计七对。',
         {'original': [4, 5, 1, 3, 2], 'sortedLeft': left, 'sortedRight': right, 'inversions': count})


def median_shrink():
    values, budget = [1, 3, 6, 8, 20], 3
    states, left, best = [], 0, 0
    for right in range(len(values)):
        while True:
            mid = (left + right) // 2
            contributions = [abs(v - values[mid]) if left <= k <= right else 0
                             for k, v in enumerate(values)]
            cost = sum(contributions)
            valid = cost <= budget
            if valid:
                best = max(best, right - left + 1)
            note = (f'窗口 [{left + 1},{right + 1}] 的最小费用为 {cost}，不超过预算 {budget}；记录长度后继续扩右端。' if valid else
                    f'窗口最小费用 {cost} 超过预算 {budget}；即使改到中位数仍不够，移出左端 {values[left]}。')
            states.append((left, right, mid, contributions, cost, best, note))
            if valid:
                break
            left += 1
    assert best == 2
    frames = []
    for step, (left, right, mid, terms, cost, best, note) in enumerate(states):
        frame, draw = canvas('加减：中位数费用决定窗口是否需要缩短', step, len(states), note)
        array(draw, values, y=135, cell=175, active=range(left, right + 1), invalid=range(left),
              labels=[str(i + 1) for i in range(len(values))])
        text(draw, (38, 220), f'当前中位数：{values[mid]}    预算：{budget}', 26, BLUE)
        text(draw, (38, 274), '各项修改次数', 22, MUTED)
        array(draw, [str(terms[k]) if left <= k <= right else '—' for k in range(5)],
              y=312, cell=175, active=[mid])
        text(draw, (38, 397), f'总费用 {cost}     当前最长可行长度 {best}', 24, TEAL if cost <= budget else RED)
        frames.append(frame)
    save('median-window-shrink', frames, [224938],
         '用已排序的 1、3、6、8、20 和预算三展示扩张、计算中位数费用、移出左端再检查的完整过程。',
         {'sorted': values, 'budget': budget, 'maximumCount': best})


def mo_pairs():
    colors = [1, 2, 3, 3, 3, 2]
    queries = [(2, 6), (1, 3), (3, 5), (1, 6)]
    block = int(math.sqrt(len(colors)))
    order = sorted(range(len(queries)), key=lambda i: (
        queries[i][0] // block,
        queries[i][1] if queries[i][0] // block % 2 == 0 else -queries[i][1]))
    left, right, pairs = 1, 0, 0
    counts, states, answers = [0, 0, 0, 0], [], [None] * 4

    def snapshot(note):
        actual = colors[left - 1:right]
        assert counts[1:] == [actual.count(c) for c in range(1, 4)]
        assert pairs == sum(n * (n - 1) // 2 for n in counts)
        states.append((left, right, counts[:], pairs, answers[:], note))

    def add(position, side):
        nonlocal pairs
        color = colors[position - 1]
        before = counts[color]
        pairs += before
        counts[color] += 1
        snapshot(f'{side}加入位置 {position} 的颜色 {color}。原来有 {before} 只同色袜子，新增 {before} 对。')

    def remove(position, side):
        nonlocal pairs
        color = colors[position - 1]
        counts[color] -= 1
        pairs -= counts[color]
        snapshot(f'{side}移出位置 {position} 的颜色 {color}。先减频次，再减去剩余 {counts[color]} 只对应的同色对。')

    snapshot('先按莫队顺序重排询问；输出仍会放回每个询问原来的编号。当前窗口为空。')
    for identity in order:
        target_left, target_right = queries[identity]
        while left > target_left:
            left -= 1
            add(left, '左端')
        while right < target_right:
            right += 1
            add(right, '右端')
        while left < target_left:
            removed = left
            left += 1
            remove(removed, '左端')
        while right > target_right:
            removed = right
            right -= 1
            remove(removed, '右端')
        length = right - left + 1
        total = length * (length - 1) // 2
        divisor = math.gcd(pairs, total)
        answers[identity] = f'{pairs // divisor}/{total // divisor}' if pairs else '0/1'
        snapshot(f'原第 {identity + 1} 个询问 [{left},{right}]：同色对 {pairs}，全部对 {total}，约分得 {answers[identity]}。')
    assert answers == ['2/5', '0/1', '1/1', '4/15']
    frames = []
    for step, (left, right, count, pairs, answers, note) in enumerate(states):
        frame, draw = canvas('小 Z 的袜子：移动端点，只更新一种颜色的配对', step, len(states), note)
        array(draw, colors, y=130, cell=140, active=range(left - 1, right),
              labels=[str(i + 1) for i in range(len(colors))])
        text(draw, (38, 220), f'窗口 [{left},{right}]' if left <= right else '窗口为空', 24, BLUE)
        for c in range(1, 4):
            box(draw, (38 + (c - 1) * 205, 265, 228 + (c - 1) * 205, 323),
                f'颜色{c}：{count[c]}只', fill=ACTIVE, size=22)
        text(draw, (700, 278), f'同色对 {pairs}', 25, TEAL)
        text(draw, (38, 365), '按原编号存回：' + '   '.join(x or '?' for x in answers), 24)
        frames.append(frame)
    save('mo-socks-pairs', frames, [51115],
         '使用原样例展示按莫队顺序移动左右端点；绿色为窗口，加入先算新增对，删除先减频次。',
         {'colors': colors, 'originalQueries': queries, 'processingOrder': [i + 1 for i in order],
          'answers': answers})


if __name__ == '__main__':
    forced_columns()
    merge_count()
    median_shrink()
    mo_pairs()
    attach()
    print(json.dumps({'newAnimations': len(RECORDS), 'newFrames': sum(x['frames'] for x in RECORDS),
                      'allTraceAssertionsPassed': True}))
