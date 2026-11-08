"""An asserted failure-tree activation trace for the dynamic-border editorial."""
from nowcoder_animations import (ACTIVE, BLUE, DEAD, INK, MUTED, RECORDS, TEAL,
                                attach, box, canvas, save, text)


def run():
    final = 'ababa'
    pi = [0] * len(final)
    for i in range(1, len(final)):
        j = pi[i - 1]
        while j and final[i] != final[j]:
            j = pi[j - 1]
        pi[i] = j + (final[i] == final[j])
    parent = [0] + pi
    assert parent == [0, 0, 0, 1, 2, 3]
    states = []

    def snapshot(current, focus, chain, note):
        counts = [0] * 6
        for end in range(1, current + 1):
            node = end
            while node:
                counts[node] += 1
                node = parent[node]
        for length in range(1, 6):
            brute = sum(final[start:start + length] == final[:length]
                        for start in range(max(0, current - length + 1)))
            assert counts[length] == brute
        states.append((current, counts, focus, chain, note))

    snapshot(0, None, [], '先按最终串 ababa 建失败树。每个编号表示一个前缀长度；尚未真正出现的结点保持灰色。')
    snapshot(4, None, [], '当前串 abab，只激活结束位置1到4。前缀 a 出现2次，ab出现2次，aba出现1次。')
    snapshot(5, 5, [5, 3, 1], '追加 a，只激活新结束位置5。新出现的后缀依次为 ababa、aba、a，对应5→3→1。')
    snapshot(5, 3, [3, 5], '数前缀 aba：它的失败树子树中，激活结点3和5对应两次出现，结束位置分别为3、5。')
    snapshot(5, 5, [5], '查询 k=2。先看整个串，长度5只出现1次，不够；沿失败祖先链找更短的前后缀。')
    snapshot(5, 3, [5, 3], '长度3的 aba 出现2次，已经满足。它是当前祖先链上最长的合格者，答案为3。')
    snapshot(5, 3, [5, 3, 1], '再查询 k=3。长度5和3的出现次数都不足3，继续跳到长度1。')
    snapshot(5, 1, [5, 3, 1], '长度1的 a 出现3次，答案为1。树中有未来结点不等于它已出现，统计只看已激活的结束位置。')
    assert states[1][1] == [0, 2, 2, 1, 1, 0]
    assert states[2][1] == [0, 3, 2, 2, 1, 1]
    coordinates = [(330, 115), (210, 195), (450, 195), (210, 275), (450, 275), (210, 355)]
    frames = []
    for step, (current, counts, focus, chain, note) in enumerate(states):
        frame, draw = canvas('动态前后缀：建最终树，按实际时刻激活', step, len(states), note)
        for node in range(1, 6):
            x, y = coordinates[node]
            px, py = coordinates[parent[node]]
            draw.line((px, py + 22, x, y - 22), fill=TEAL if node in chain else '#bdcadd', width=4)
        for node, (x, y) in enumerate(coordinates):
            label = f'{node} / ' + (final[:node] if node else '空')
            box(draw, (x - 86, y - 22, x + 86, y + 22), label,
                fill=ACTIVE if 0 < node <= current else DEAD,
                outline=BLUE if node == focus else None, size=19)
        text(draw, (600, 106), '当前串：' + (final[:current] or '空'), 23, BLUE)
        text(draw, (600, 154), '前缀长度    出现次数', 21, MUTED)
        for node in range(1, 6):
            color = BLUE if node == focus else INK
            text(draw, (637, 175 + node * 35), f'{node}                 {counts[node]}', 23, color)
        text(draw, (36, 405), '绿色：已激活   灰色：尚未出现   蓝框：正在检查', 20, MUTED)
        frames.append(frame)
    save('failure-tree-activation', frames, [233500],
         '以 abab 追加 a 为例，展示结束位置激活、失败树子树计数，以及 k=2、k=3 时沿祖先链找答案。',
         {'finalString': final, 'initialLength': 4, 'append': 'a', 'failureParents': parent,
          'beforeCounts': states[1][1], 'afterCounts': states[2][1], 'queries': [[2, 3], [3, 1]]})
    attach()
    print('Checked and attached', len(frames), 'failure-tree frames.')


if __name__ == '__main__':
    run()
