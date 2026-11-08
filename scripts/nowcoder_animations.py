"""Generate exact, local GIF diagrams from checked algorithm traces.

Run with Windows Python/Pillow. These are data-driven diagrams, not generated
photographs: every answer, pointer and matrix cell is checked before drawing.
"""
from functools import lru_cache
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont

from nowcoder_editorials import CONTENT, OUT, ROOT, read, write, sha, program

WIDTH, HEIGHT = 940, 540
BG, INK, MUTED = '#f7f9fc', '#243449', '#69798e'
TEAL, BLUE, RED = '#12806b', '#2863ac', '#bd4c43'
SOFT, ACTIVE, DEAD = '#e4edf7', '#d3efe7', '#e6e9ee'
ASSETS = CONTENT / 'assets'
RECORDS = []


@lru_cache(maxsize=12)
def font(size=23):
    return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', size)


def text(draw, xy, value, size=23, fill=INK, anchor=None):
    draw.text(xy, str(value), font=font(size), fill=fill, anchor=anchor)


def wrap(draw, xy, value, width=860, size=22, fill=INK):
    x, y = xy
    line = ''
    for char in value:
        if char == '\n' or font(size).getlength(line + char) > width:
            text(draw, (x, y), line, size, fill)
            line = '' if char == '\n' else char
            y += size + 12
        else:
            line += char
    if line:
        text(draw, (x, y), line, size, fill)
    return y + size + 12


def canvas(title, step, total, note):
    image = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    text(draw, (32, 22), title, 28)
    text(draw, (WIDTH - 32, 39), f'{step + 1} / {total}', 20, MUTED, 'rm')
    draw.line((32, 72, WIDTH - 32, 72), fill='#d7e0eb', width=2)
    wrap(draw, (32, 439), note, size=22)
    return image, draw


def box(draw, bounds, label, *, fill=SOFT, color=INK, outline=None, size=25):
    draw.rounded_rectangle(bounds, radius=10, fill=fill, outline=outline, width=3)
    x1, y1, x2, y2 = bounds
    text(draw, ((x1 + x2) / 2, (y1 + y2) / 2), label, size, color, 'mm')


def array(draw, values, *, y=130, active=(), invalid=(), labels=None, cell=83, x=38):
    for i, value in enumerate(values):
        fill = ACTIVE if i in active else DEAD if i in invalid else SOFT
        box(draw, (x + i * cell, y, x + i * cell + cell - 10, y + 58), value,
            fill=fill, outline=TEAL if i in active else None)
        if labels:
            text(draw, (x + i * cell + (cell - 10) / 2, y - 20), labels[i], 17, MUTED, 'mm')


def save(name, frames, ids, description, scenario, durations=None):
    ASSETS.mkdir(parents=True, exist_ok=True)
    # One shared palette keeps still regions and font edges stable between frames.
    sheet = Image.new('RGB', (235 * len(frames), 135), BG)
    for i, frame in enumerate(frames):
        sheet.paste(frame.resize((235, 135)), (235 * i, 0))
    palette = sheet.quantize(colors=192)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    timings = durations or [1400] + [900] * (len(frames) - 2) + [2600]
    path = ASSETS / (name + '.gif')
    indexed[0].save(path, save_all=True, append_images=indexed[1:], duration=timings,
                    loop=0, optimize=True, disposal=2)
    frames[0].save(ASSETS / (name + '.png'))
    with Image.open(path) as gif:
        assert gif.n_frames > 1 and gif.size == (WIDTH, HEIGHT)
        decoded = []
        for i in range(gif.n_frames):
            gif.seek(i)
            decoded.append(sha(gif.convert('RGB').tobytes()))
        assert len(set(decoded)) > 1
    record = {'name': name, 'problemIds': ['nowcoder-global::' + str(x) for x in ids],
               'file': str(path.relative_to(ROOT)).replace('\\', '/'),
               'frames': len(frames), 'durationMs': sum(timings), 'sha256': sha(path.read_bytes()),
               'description': description, 'scenario': scenario}
    RECORDS.append(record)
    return record


def monotonic_stack():
    values = [3, 2, 6, 1, 1, 2]
    stack, answers, states = [], [None] * len(values), []
    states.append((-1, [], answers[:], '从右往左处理；栈中只留仍可能成为答案的位置。'))
    for i in range(len(values) - 1, -1, -1):
        states.append((i, stack[:], answers[:], f'现在处理位置 {i + 1}，数值为 {values[i]}。'))
        while stack and values[stack[-1]] <= values[i]:
            removed = stack.pop()
            states.append((i, stack[:], answers[:],
                           f'弹出位置 {removed + 1}：它的数值 {values[removed]} 不大于 {values[i]}，不能回答当前查询。'))
        answers[i] = stack[-1] + 1 if stack else 0
        states.append((i, stack[:], answers[:],
                       f'当前位置答案为 {answers[i]}。零表示右侧没有更大数；随后把位置 {i + 1} 入栈。'))
        stack.append(i)
        states.append((i, stack[:], answers[:], f'位置 {i + 1} 已入栈，继续处理它左边的位置。'))
    assert answers == [3, 3, 0, 6, 6, 0]
    frames = []
    for step, (current, st, ans, note) in enumerate(states):
        image, draw = canvas('右侧第一个更大数：弹出、取栈顶、入栈', step, len(states), note)
        array(draw, values, active=[current], labels=[f'位置 {i + 1}' for i in range(6)])
        text(draw, (38, 214), '已确定答案', 21, MUTED)
        array(draw, ['?' if x is None else x for x in ans], y=250, cell=83)
        text(draw, (38, 340), '候选栈：底 → 顶', 21, MUTED)
        for j, idx in enumerate(st):
            box(draw, (270 + j * 140, 326, 400 + j * 140, 390), f'{idx + 1} : {values[idx]}',
                fill=ACTIVE if j == len(st) - 1 else SOFT, size=22)
        if not st:
            text(draw, (280, 344), '空', 24, MUTED)
        frames.append(image)
    save('monotonic-stack', frames, [18356], '相同数值也要弹出；栈里保存下标，而不是只保存数值。', {'array': values, 'answers': answers})


def sliding_window():
    values, k = [1, 3, -1, -3, 5, 3, 6, 7], 3
    qmin, qmax, states, mins, maxs = [], [], [], [], []
    for right, value in enumerate(values):
        left = max(0, right - k + 1)
        while qmin and qmin[0] < left:
            qmin.pop(0)
        while qmax and qmax[0] < left:
            qmax.pop(0)
        while qmin and values[qmin[-1]] >= value:
            qmin.pop()
        while qmax and values[qmax[-1]] <= value:
            qmax.pop()
        qmin.append(right)
        qmax.append(right)
        if right >= k - 1:
            mins.append(values[qmin[0]])
            maxs.append(values[qmax[0]])
            assert mins[-1] == min(values[left:right + 1])
            assert maxs[-1] == max(values[left:right + 1])
        states.append((left, right, qmin[:], qmax[:], mins[:], maxs[:]))
    frames = []
    for step, (left, right, low, high, a, b) in enumerate(states):
        note = '窗口尚未填满，先维护候选。' if right < k - 1 else f'窗口 [{left + 1}, {right + 1}]：最小值 {a[-1]}，最大值 {b[-1]}。过期下标从队首移出。'
        image, draw = canvas('窗口右移：队首始终给出当前极值', step, len(states), note)
        array(draw, values, active=range(left, right + 1), invalid=range(left), cell=108,
              labels=[str(i + 1) for i in range(len(values))])
        for y, label, queue in [(230, '最小值队列', low), (315, '最大值队列', high)]:
            text(draw, (38, y + 17), label, 22)
            for j, idx in enumerate(queue):
                box(draw, (225 + 130 * j, y, 345 + 130 * j, y + 58), f'{idx + 1}:{values[idx]}',
                    fill=ACTIVE if j == 0 else SOFT, size=23)
        frames.append(image)
    assert mins == [-1, -3, -3, -3, 3, 3] and maxs == [3, 3, 5, 5, 6, 7]
    save('sliding-window', frames, [50528, 51001], '方块中的“下标:数值”对应正文中的单调队列；绿色队首是当前答案。', {'array': values, 'window': k, 'minimum': mins, 'maximum': maxs})


def matrix_timestamps():
    operations = [(1, 1, 3), (2, 1, 1), (1, 0, 3)]
    rt, ct, rv, cv = [0] * 3, [0] * 3, [0] * 3, [0] * 3
    states, literal = [], [[0] * 3 for _ in range(3)]
    states.append(([row[:] for row in literal], rt[:], ct[:], None, '初始矩阵全零，所有行列时间戳都是零。'))
    for time, (op, k, value) in enumerate(operations, 1):
        if op == 1:
            rt[k], rv[k] = time, value
            for j in range(3):
                literal[k][j] = value
        else:
            ct[k], cv[k] = time, value
            for i in range(3):
                literal[i][k] = value
        actual = [[rv[i] if rt[i] > ct[j] else cv[j] for j in range(3)] for i in range(3)]
        assert actual == literal
        states.append((actual, rt[:], ct[:], (op, k), f'第 {time} 次：把第 {k + 1}{"行" if op == 1 else "列"} 赋成 {value}。较晚的操作覆盖较早的操作。'))
    final = [row[:] for row in literal]
    states.append((final, rt[:], ct[:], (3, (1, 1)), '格子 (2,2)：列最后在时刻 2 赋一，行最后在时刻 1 赋三。取较晚的列，所以值为一。'))
    states.append((final, rt[:], ct[:], (3, (0, 1)), '格子 (1,2)：行最后在时刻 3 赋三，晚于列的时刻 2。因此最终值为三。'))
    frames = []
    for step, (matrix, rows, cols, selected, note) in enumerate(states):
        image, draw = canvas('行列覆盖：每格只比较两个最后时刻', step, len(states), note)
        for i in range(3):
            for j in range(3):
                active = selected and ((selected[0] == 1 and i == selected[1]) or
                                       (selected[0] == 2 and j == selected[1]) or
                                       (selected[0] == 3 and (i, j) == selected[1]))
                box(draw, (50 + j * 100, 125 + i * 85, 140 + j * 100, 200 + i * 85), matrix[i][j], fill=ACTIVE if active else SOFT)
        text(draw, (425, 135), '行最后修改时刻', 24)
        text(draw, (425, 185), str(rows), 26, TEAL)
        text(draw, (425, 267), '列最后修改时刻', 24)
        text(draw, (425, 317), str(cols), 26, BLUE)
        frames.append(image)
    assert final == [[3, 3, 3], [3, 1, 3], [0, 1, 0]]
    save('matrix-timestamps', frames, [13883], '绿色标出当前覆盖的行、列或正在比较的格子，旁边是实际时间戳。', {'operations': operations, 'finalMatrix': final})


def necklace():
    states = [([10, 2, 3, 5, 10], 0, '四颗珠子是四条边，五个圆表示它们的头尾标记；切口选在十。'),
              ([10, 3, 5, 10], 60, '合并 10→2 与 2→3，接缝二消去，增加 10×2×3=60。'),
              ([10, 5, 10], 210, '再与 3→5 合并，接缝三消去，增加 10×3×5=150，累计 210。'),
              ([10, 10], 710, '最后合并，接缝五消去，增加 10×5×10=500，总能量为 710。')]
    frames = []
    for step, (nodes, energy, note) in enumerate(states):
        image, draw = canvas('能量项链：消去的是接缝，保留外侧端点', step, len(states), note)
        positions = [90 + i * 180 for i in range(len(nodes))]
        for i in range(len(nodes) - 1):
            draw.line((positions[i], 210, positions[i + 1], 210), fill=TEAL, width=8)
        for i, value in enumerate(nodes):
            color = BLUE if i == 0 or i == len(nodes) - 1 else TEAL
            draw.ellipse((positions[i] - 30, 180, positions[i] + 30, 240), fill='white', outline=color, width=4)
            text(draw, (positions[i], 210), value, 25, color, 'mm')
        text(draw, (42, 300), f'累计能量：{energy}', 30, TEAL)
        text(draw, (42, 363), '示例展示一条最优合并路线；区间 DP 还要比较其他切口与合并次序。', 20, MUTED)
        frames.append(image)
    def best(a):
        if len(a) == 2:
            return 0
        return max(best(a[:k + 1]) + best(a[k:]) + a[0] * a[k] * a[-1]
                   for k in range(1, len(a) - 1))
    assert best([10, 2, 3, 5, 10]) == 710
    save('necklace-merge', frames, [16670], '圆是边界标记，线段才是一颗珠；合并不把两个外侧标记删掉。', {'boundaryLabels': [10, 2, 3, 5, 10], 'energy': 710})


def end_picking():
    values = [1, 2, 3]
    first, second = [0, 1, 2], [2, 0, 1]
    assert all(values[i] == i + 1 for i in range(3))
    frames = []
    for step in range(4):
        notes = ['同一行每次只能取当前最左或最右，越晚取的数乘上的权重越大。',
                 '第一次权重为二：上面取左侧一，下面取右侧三。',
                 '第二次权重为四：取掉后，两条路线剩余区间已经不同。',
                 '第三次权重为八：上面总分三十四，下面二十六，说明优先取大数未必最优。']
        image, draw = canvas('矩阵取数：剩余区间与取数轮次一起变化', step, 4, notes[step])
        for y, route, label in [(140, first, '最优路线'), (285, second, '对照路线')]:
            total = sum(values[route[i]] * (1 << (i + 1)) for i in range(step))
            text(draw, (35, y + 15), label, 23)
            array(draw, values, y=y, x=190, cell=115, invalid=route[:step])
            chosen = ' → '.join(str(values[route[i]]) for i in range(step)) or '尚未取数'
            text(draw, (590, y + 3), f'已取：{chosen}', 22)
            text(draw, (590, y + 48), f'累计：{total}', 25, TEAL)
        frames.append(image)
    assert sum(values[first[i]] * 2 ** (i + 1) for i in range(3)) == 34
    save('interval-end-picking', frames, [16645], '只展示一行即可看清两端选择如何改变后续区间；各行仍独立求最优后相加。', {'row': values, 'optimalOrder': [1, 2, 3], 'score': 34})


def josephus():
    people, pointer, states = list(range(5)), 1, []
    states.append((people[:], 1, None, '从编号一的人开始报一，报二的人离开，下一人重新从一开始。'))
    while len(people) > 1:
        states.append((people[:], people[pointer], None, f'编号 {people[pointer]} 报一。'))
        victim_index = (pointer + 1) % len(people)
        victim = people[victim_index]
        states.append((people[:], victim, victim, f'编号 {victim} 报二，即将出队。'))
        people.pop(victim_index)
        pointer = victim_index % len(people)
        states.append((people[:], people[pointer], None, f'移除编号 {victim}；下一轮由编号 {people[pointer]} 重新报一。'))
    assert people == [3]
    frames = []
    import math
    for step, (remaining, active, victim, note) in enumerate(states):
        image, draw = canvas('约瑟夫环：报数跳过已经离开的人', step, len(states), note)
        coordinates = [(470 + 145 * math.sin(2 * math.pi * i / 5), 255 - 145 * math.cos(2 * math.pi * i / 5)) for i in range(5)]
        for i, (x, y) in enumerate(coordinates):
            fill = ACTIVE if i == active else SOFT if i in remaining else DEAD
            outline = RED if i == victim else TEAL if i == active else '#b6c2d0'
            draw.ellipse((x - 33, y - 33, x + 33, y + 33), fill=fill, outline=outline, width=4)
            text(draw, (x, y), i, 27, INK if i in remaining else MUTED, 'mm')
        text(draw, (470, 255), f'还剩 {len(remaining)} 人', 24, TEAL, 'mm')
        frames.append(image)
    save('josephus-counting', frames, [22227], '原编号一直保留，报数时只沿仍在队伍中的人继续，最后剩编号三。', {'n': 5, 'start': 1, 'count': 2, 'survivor': 3})


def reverse_buttons():
    backward = [20, 9, 4, 1, 0]
    reverse_keys = ['G', 'N', 'G', 'N']
    forward = [0, 1, 4, 9, 20]
    keys = ''.join(reversed(reverse_keys))
    assert keys == 'NGNG'
    for i, key in enumerate(keys):
        assert forward[i] * 2 + (1 if key == 'N' else 2) == forward[i + 1]
    states = [('back', i) for i in range(5)] + [('forward', i) for i in range(5)]
    frames = []
    for step, (phase, progress) in enumerate(states):
        note = ('逆推时，奇数只能来自 N，偶数只能来自 G。此时记下的是最后一次、倒数第二次……按键。'
                if phase == 'back' else '逆推记录 GNGN 反转为 NGNG，再从零正向执行，可以精确得到二十。')
        image, draw = canvas('勇气获得机：先倒着找按钮，再反转顺序', step, len(states), note)
        text(draw, (38, 105), '从目标逆推', 23)
        array(draw, backward, y=145, x=38, cell=170,
              active=[progress] if phase == 'back' else [])
        text(draw, (38, 222), '逆序按钮：' + ''.join(reverse_keys[:progress] if phase == 'back' else reverse_keys), 23, BLUE)
        text(draw, (38, 280), '从零正向核对', 23)
        array(draw, forward, y=322, x=38, cell=170,
              active=[progress] if phase == 'forward' else [])
        frames.append(image)
    save('reverse-buttons', frames, [14710], '逆推找到的 GNGN 需要反转；图中把逆向数值和正向核对分成两行。', {'target': 20, 'backward': backward, 'forward': forward, 'buttons': keys})


def tree_traversal():
    inorder, postorder, output, calls, states = 'BADC', 'BDCA', [], [], []
    def snapshot(note):
        states.append(([dict(x) for x in calls], ''.join(output), note))
    def visit(mid, post):
        if not mid:
            return
        root = post[-1]
        k = mid.index(root)
        calls.append({'mid': mid, 'post': post, 'root': root})
        snapshot(f'后序串 {post} 的最后字符 {root} 是当前子树根。')
        output.append(root)
        snapshot(f'先序先输出根 {root}；中序串由根分成左边 {mid[:k] or "空"} 与右边 {mid[k + 1:] or "空"}。')
        visit(mid[:k], post[:k])
        if mid[:k]:
            snapshot(f'{root} 的左子树处理完并返回，再处理右子树。')
        visit(mid[k + 1:], post[k:-1])
        calls.pop()
        snapshot(f'以 {root} 为根的子问题返回。')
    visit(inorder, postorder)
    assert ''.join(output) == 'ABCD'
    frames = []
    for step, (stack, result, note) in enumerate(states):
        image, draw = canvas('先序恢复：每一层递归只管理自己的区间', step, len(states), note)
        text(draw, (38, 102), '递归调用：外层 → 当前层', 23, MUTED)
        for depth, call in enumerate(stack):
            box(draw, (40 + depth * 35, 147 + depth * 74, 890, 209 + depth * 74),
                f'中序 {call["mid"]}    后序 {call["post"]}    根 {call["root"]}',
                fill=ACTIVE if depth == len(stack) - 1 else SOFT, size=24)
        text(draw, (38, 390), '已经输出：' + (result or '空'), 27, TEAL)
        frames.append(image)
    save('tree-recursion', frames, [16692], '动态展示分割、进入左子树、返回和继续右子树，输出顺序与程序的先序访问一致。', {'inorder': inorder, 'postorder': postorder, 'preorder': ''.join(output)})


def attach():
    ledger = read(CONTENT / 'reviewed.json')
    for record in RECORDS:
        for identity in record['problemIds']:
            entry = ledger[identity]
            for file in entry['articles'].values():
                path = ROOT / file
                original = path.read_text(encoding='utf-8')
                marker = '<!-- nowcoder-animation:' + record['name'] + ' -->'
                if marker in original:
                    continue
                block = ('\n\n' + marker + '\n\n### 动态示例\n\n' +
                         '![' + record['description'] + '](assets/' + record['name'] + '.gif)\n\n' +
                         record['description'] + '\n\n')
                location = original.index('### 参考代码')
                updated = original[:location].rstrip() + block + original[location:]
                assert program(updated) == program(original)
                path.write_text(updated, encoding='utf-8')
            entry['animations'] = list(dict.fromkeys([*entry.get('animations', []), record['file']]))
    write(CONTENT / 'reviewed.json', ledger)
    path = CONTENT / 'animations.json'
    merged = {x['name']: x for x in read(path)} if path.exists() else {}
    merged.update({x['name']: x for x in RECORDS})
    write(path, list(merged.values()))


if __name__ == '__main__':
    monotonic_stack()
    sliding_window()
    matrix_timestamps()
    necklace()
    end_picking()
    josephus()
    reverse_buttons()
    tree_traversal()
    attach()
    print(json.dumps({'animations': len(RECORDS), 'articleProblems': sum(len(x['problemIds']) for x in RECORDS),
                      'frames': sum(x['frames'] for x in RECORDS), 'allTraceAssertionsPassed': True}))
