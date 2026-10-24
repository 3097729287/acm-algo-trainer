"""Assemble reviewed text, verified code and native SVG figures for 2026-10-24."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/contests/20261024'
CONTESTS = {
    'abc481': {'series': 'ABC', 'number': 481, 'platform': 'AtCoder', 'url': 'https://atcoder.jp/contests/abc481', 'range': 'A-F',
        'problems': [('A', 'Digits of A+B', '模拟', 800), ('B', 'Polyline', '计算几何', 800), ('C', 'Bank Accounts', '模拟', 800), ('D', 'Autopilot', '最短路', 1000), ('E', 'Most Brilliant Starry Sky', '计算几何[主] + 双指针 + 排序', 1500), ('F', 'Evil Shortest Path', 'BFS[主] + 贪心', 1700)],
        'record': '编译：A—F 均通过 C++17、-O2、-Wall、-Wextra 检查，无警告。\n官方样例：A—F 分别 3、3、2、3、1、3 组全过。\n边界用例：A—F 分别 81、4、2、4、4、3 条全过。\n随机对拍：A—F 分别实跑 300、300、300、500、1500、500 组，全一致（seed=20261024）。\n极限计时：A—F 分别 0.005、0.006、0.088、0.045、0.033、0.074 s，均通过题面时限。'},
    'month311': {'series': '月赛', 'number': 311, 'platform': '洛谷', 'url': 'https://www.luogu.com.cn/contest/364653', 'range': 'A-C',
        'problems': [('A', '极差 / Range', '构造', 1150), ('C', '位运算 / Bit', '位运算[主] + 贪心 + 快速幂', 2050)],
        'record': '编译：A、C 均通过 C++17、-O2、-Wall、-Wextra 检查，无警告。\n官方样例：A、C 各 2 组全过；A 使用合法性判定器。\n边界用例：A 的 5 条、C 的 2 条全过；C 包含 3072 组小范围约束的独立穷举。\n随机对拍：A 实跑 300 组，C 实跑 500 组，全一致（seed=20261024）。\n极限计时：A 的百万长度为 0.093 s；C 的五十万组、60 位及大规模参数为 0.627 s，均通过题面时限。'},
}


def label(x, y, value, size=19, color='#223344', anchor='middle'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(str(value))}</text>'


def line(x1, y1, x2, y2, color='#61758a', width=2, dashed=False, arrow=False):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"' + (' stroke-dasharray="7 5"' if dashed else '') + (' marker-end="url(#arrow)"' if arrow else '') + '/>'


def node(x, y, name, fill='#e6f4f0'):
    return f'<circle cx="{x}" cy="{y}" r="24" fill="{fill}" stroke="#397c6e" stroke-width="2"/>' + label(x, y + 7, name)


def svg(path, title, body, height=360):
    path.parent.mkdir(parents=True, exist_ok=True)
    value = f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}" role="img"><title>{escape(title)}</title><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="#61758a"/></marker></defs><rect width="720" height="{height}" rx="14" fill="#f7fafc"/><g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif">' + label(360, 32, title, 21) + body + '</g></svg>'
    path.write_text(value, encoding='utf-8')


def figures():
    p = BASE / 'abc481/images'
    body = line(75, 280, 660, 280, arrow=True) + line(95, 290, 95, 65, arrow=True)
    body += line(95, 105, 650, 105, '#d59a25', 2, True) + label(620, 90, 'y = K = 3')
    body += '<polyline points="170,245 360,105 550,245" fill="none" stroke="#397c6e" stroke-width="4"/>'
    for x, y, name in [(170,245,'(1,1)'),(360,105,'(2,3)'),(550,245,'(3,1)')]:
        body += f'<circle cx="{x}" cy="{y}" r="6" fill="#397c6e"/>' + label(x, y + (29 if y > 200 else -20), name)
    body += label(360, 325, '共享折点计 1 次；两条线段内部都没有交点')
    svg(p/'b-vertex.svg', '折点和线段内部交点分开计数', body)
    body = line(155, 152, 295, 152, '#397c6e', 3, arrow=True) + line(295, 178, 155, 178, '#397c6e', 3, arrow=True)
    body += line(150, 190, 305, 270, '#d18625', 3, arrow=True) + line(350, 270, 550, 185, '#397c6e', 3, arrow=True)
    for x,y,n in [(130,165,1),(325,165,2),(325,280,3),(580,170,4)]: body += node(x,y,n)
    body += label(225, 130, '0（免费）') + label(225, 210, '0') + label(205, 270, '1（付费）') + label(470, 260, '0')
    body += label(360, 75, '目标：从 1 到 4') + label(360, 335, '免费环 1 → 2 → 1；最优路线 1 → 3 → 4，耗油 1')
    svg(p/'d-zero-one.svg', '费用为 0 或 1 的有向航线', body, 370)
    body = '<path d="M80,65 L660,65 L660,315 L473,315 L80,156 Z" fill="#e6f4f0"/>'
    body += line(80,235,655,235,arrow=True) + line(275,320,275,70,arrow=True) + line(80,156,473,315,'#d18625',2,True)
    body += label(662,240,'x') + label(275,60,'y') + label(255,257,'O')
    for x,y,name in [(485,305,'(3,−1)'),(415,165,'(2,1)'),(345,95,'(1,2)')]:
        body += line(275,235,x,y,'#397c6e',2) + f'<circle cx="{x}" cy="{y}" r="6" fill="#397c6e"/>' + label(x+40,y-12,name,17)
    body += label(490,77,'所选一侧',18,'#397c6e') + label(360,345,'方向跨越正 x 轴，复制角度序列后仍是连续窗口',17)
    svg(p/'e-half-plane.svg', '一侧平面对应不足半圈的星星方向', body)
    body = '<rect x="270" y="75" width="145" height="225" rx="16" fill="#e6f4f0" stroke="#397c6e" stroke-dasharray="6 5"/>'
    for (x1,y1,x2,y2,d) in [(145,175,290,120,1),(145,205,290,260,1),(355,120,535,175,9),(355,260,535,205,2)]:
        body += line(x1,y1,x2,y2,arrow=True) + label((x1+x2)/2,(y1+y2)/2-8,d)
    for x,y,n in [(120,190,1),(325,110,2),(325,270,3),(565,190,4)]: body += node(x,y,n)
    body += label(343,60,'同组：前缀 1') + label(565,245,'先 12，后 19',18) + label(360,335,'先收集整个组的出边，再按末位数字 1 → 9 处理')
    svg(p/'f-groups.svg', '相同前缀必须作为一个整体展开', body)
    p = BASE / 'month311/images'
    body = ''
    values = [1,3,5,2,4]
    for i,v in enumerate(values):
        x=165+i*100;body += node(x,110,v) + node(x,245,values[(i+1)%5]) + line(x,140,x,210,arrow=True)
        if i < 4: body += line(x+28,110,x+72,110,arrow=True)
    body += '<path d="M589,110 C660,30 65,30 141,110" fill="none" stroke="#61758a" stroke-width="2" marker-end="url(#arrow)"/>'
    body += label(70,117,'a') + label(70,252,'b') + label(365,190,'循环左移一格',17) + label(360,320,'横向相邻与同列配对，都是环上的相邻数')
    svg(p/'a-cycle.svg', 'n = 5：先奇数、后偶数，再循环左移', body)
    body = label(115,85,'操作') + label(350,85,'三个实际整数') + label(600,85,'二进制')
    for y,name,values,bits in [(135,'初始','7，7，7','111  111  111'),(205,'清两个 4','7，3，3','111  011  011'),(275,'清一个 1','6，3，3','110  011  011')]:
        body += label(115,y,name,18) + label(350,y,values,21,'#397c6e') + label(600,y,bits,18)
        if y < 275: body += line(350,y+14,350,y+44,arrow=True)
    body += label(360,330,'AND = 2，OR = 7，XOR = 6；最大乘积 6 × 3 × 3 = 54')
    svg(p/'c-bits.svg', '让当前最大的数承担清零', body)


def main():
    figures()
    for folder, spec in CONTESTS.items():
        root = BASE/folder
        for variant in ['default', 'detailed']:
            name = '题解' if variant == 'default' else '详细题解'
            text = f"# {spec['series']} {spec['number']} {name}\n\n> 比赛：{spec['url']}\n> 语言：C++17\n\n## 目录\n\n| 题号 | 题名 | 考点 | 难度 |\n|---|---|---|---|\n"
            for letter,title,knowledge,rating in spec['problems']:
                text += f'| {letter} | {title} | {knowledge} | {rating} |\n'
            for letter,title,_,_ in spec['problems']:
                article = (root/'articles'/f'{letter}.{variant}.md').read_text(encoding='utf-8')
                code = (root/spec['range']/letter/f'{letter.lower()}.cpp').read_text(encoding='utf-8').rstrip()
                assert article.count('<!-- reference-code -->') == 1
                text += f'\n## {letter}. {title}\n\n' + article.replace('<!-- reference-code -->', '```cpp\n'+code+'\n```') + '\n'
            text += '\n## 实测记录\n\n'+spec['record']+'\n'
            (root/f"{spec['number']}{name}.md").write_text(text, encoding='utf-8')
    print('Composed 16 editorials with verified code and six SVG figures')


if __name__ == '__main__':
    main()
