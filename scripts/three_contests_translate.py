"""Reviewed Chinese statements; immutable formulas and sample blocks stay exact."""
import hashlib
import json
import re
import sys
from three_contests_programs import ROOT, CONTENT
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from translation import bundled_translation, TRANSLATION_FORMAT

REPLACE = {
r'There is a $5\times 5$ grid, and some of the cells are marked.':r'有一个 $5\times 5$ 的网格，其中一些格子已经被标记。',
r'The current state of the grid is given by strings $S_1,S_2,S_3,S_4,S_5$ of length $5$ consisting of `o` and `.`.':r'网格的当前状态由五个长度为 $5$、仅含 `o` 和 `.` 的字符串 $S_1,S_2,S_3,S_4,S_5$ 给出。',
r'The cell at the $i$-th row from the top and the $j$-th column from the left is marked if the $j$-th character of $S_i$ is `o`, and unmarked if it is `.`.':r'从上数第 $i$ 行、从左数第 $j$ 列的格子，当 $S_i$ 的第 $j$ 个字符为 `o` 时已经标记，为 `.` 时尚未标记。',
r'Find the minimum number of additional marks needed to achieve a bingo.':r'求最少还要标记多少个格子，才能达成 Bingo。',
r'Here, achieving a bingo means that there exist $5$ cells lined up in a single vertical, horizontal, or diagonal line, all of which are marked.':r'达成 Bingo 指存在沿竖直、水平或对角方向连续排成一条线的 $5$ 个格子，且全部已经标记。',
r'Each of $S_1,S_2,S_3,S_4,S_5$ is a string of length $5$ consisting of `o` and `.`.':r'$S_1,S_2,S_3,S_4,S_5$ 均为长度 $5$、仅含 `o` 和 `.` 的字符串。',
r'For example, you can achieve a bingo by marking the $2$ cells in the $5$-th row from the top and the $2$-nd and $3$-rd columns from the left.':r'例如，可以标记从上数第 $5$ 行、从左数第 $2$ 列和第 $3$ 列的 $2$ 个格子，以达成 Bingo。',
r'If a bingo is already achieved, no additional marks are needed, so the answer is $0$.':r'如果已经达成 Bingo，就无须增加标记，答案为 $0$。',
r'There is a grid with $H$ rows and $W$ columns. Let $(i,j)$ denote the cell at the $i$-th row from the top and the $j$-th column from the left.':r'有一个 $H$ 行 $W$ 列的网格。以 $(i,j)$ 表示从上数第 $i$ 行、从左数第 $j$ 列的格子。',
r'There are $N$ pieces placed on the grid, and the $i$-th piece is at $(R_i, C_i)$.':r'网格上放有 $N$ 枚棋子，第 $i$ 枚棋子位于 $(R_i, C_i)$。',
r'Answer $Q$ queries. Each query is of one of the following $2$ types.':r'回答 $Q$ 次查询，每次属于以下 $2$ 种类型之一。',
r'`1 u d`: Print the number of pieces placed in rows $u$ through $d$.':r'`1 u d`：输出行号从 $u$ 到 $d$，包含两端的棋子数量。',
r'`2 l r`: Print the number of pieces placed in columns $l$ through $r$.':r'`2 l r`：输出列号从 $l$ 到 $r$，包含两端的棋子数量。',
r'$(R_i, C_i) \neq (R_j, C_j)$ if $i \neq j$.':r'若 $i \neq j$，则 $(R_i, C_i) \neq (R_j, C_j)$。',
r'Each query $\mathrm{query}_q$ is given in one of the following formats:':r'每次查询 $\mathrm{query}_q$ 按以下两种格式之一给出：',
r'Print $Q$ lines. The $i$-th line should contain the answer to the $i$-th query.':r'输出 $Q$ 行，第 $i$ 行为第 $i$ 次查询的答案。',
r'For the $1$-st query, the pieces in rows $2$ through $4$ are the $2$-nd, $3$-rd, and $4$-th pieces, for a total of $3$.':r'对于第 $1$ 次查询，行号从 $2$ 到 $4$ 的棋子是第 $2$、第 $3$ 和第 $4$ 枚，共 $3$ 枚。',
r'There are $N$ people, numbered $1$ to $N$, standing on a number line.':r'数轴上站着 $N$ 个人，编号从 $1$ 到 $N$。',
r'Person $i$ is standing at coordinate $X_i$. Here, $X_i$ is even for $i=1,2,\dots,N$, and $X_1 < X_2 < \cdots < X_N$ holds.':r'第 $i$ 个人站在坐标 $X_i$。对 $i=1,2,\dots,N$，$X_i$ 均为偶数，并且满足 $X_1 < X_2 < \cdots < X_N$。',
r'For each $k=1,2,\dots,N$, solve the following problem.':r'对每个 $k=1,2,\dots,N$，分别解决以下问题。',
r'At time $0$, person $k$ becomes a zombie. Everyone other than person $k$ remains human.':r'在时刻 $0$，第 $k$ 个人变为感染者，除第 $k$ 个人外的所有人仍为普通人。',
r'From time $0$ onward, humans and zombies can move freely on the number line at a speed of at most $1$ per unit time.':r'从时刻 $0$ 开始，普通人和感染者均可以在数轴上自由移动，每单位时间速度不超过 $1$。',
r'When a zombie and a human are at the same coordinate, that human becomes a zombie.':r'当感染者与普通人处于同一坐标时，该普通人也变为感染者。',
r'Find the minimum possible time at which everyone has become a zombie.':r'求所有人均变为感染者的最早可能时刻。',
r'It can be proved that the answer is an integer under the constraints of this problem.':r'可以证明，在本题约束下答案为整数。',
r'$X_i$ is even.':r'$X_i$ 为偶数。',
r'Print $N$ lines. The $i$-th line $(1 \leq i \leq N)$ should contain the answer to the problem for $k=i$.':r'输出 $N$ 行。第 $i$ 行 $(1 \leq i \leq N)$ 输出初始感染者为 $k=i$ 时的答案。',
r'For $k=1$, if person $1$ moves in the positive direction of the number line at speed $1$ and persons $2,3,4,5$ move in the negative direction at speed $1$, everyone will have become a zombie by time $8$.':r'对于 $k=1$，若第 $1$ 个人以速度 $1$ 向数轴正方向移动，第 $2,3,4,5$ 个人以速度 $1$ 向负方向移动，则到时刻 $8$ 所有人都已感染。',
r'For $k=2$, if each person moves as follows, everyone will have become a zombie by time $7$.':r'对于 $k=2$，若每个人按以下方式移动，则到时刻 $7$ 所有人都已感染。',
r'Person $1$: Moves in the positive direction at speed $1$.':r'第 $1$ 个人：以速度 $1$ 向正方向移动。',
r'Person $2$: Moves in the positive direction at speed $1$ until time $3$, and in the negative direction at speed $1$ from time $3$ onward.':r'第 $2$ 个人：到时刻 $3$ 为止以速度 $1$ 向正方向移动，从时刻 $3$ 起以速度 $1$ 向负方向移动。',
r'Person $3$: Moves in the negative direction at speed $1$ until time $3$, and in the positive direction at speed $1$ from time $3$ onward.':r'第 $3$ 个人：到时刻 $3$ 为止以速度 $1$ 向负方向移动，从时刻 $3$ 起以速度 $1$ 向正方向移动。',
r'Person $4$: Moves in the negative direction at speed $1$.':r'第 $4$ 个人：以速度 $1$ 向负方向移动。',
r'Person $5$: Moves in the negative direction at speed $1$.':r'第 $5$ 个人：以速度 $1$ 向负方向移动。',
r'You are given a tree $T$ with $N$ vertices numbered $1,2,\dots,N$. For $i=1,2,\dots,N-1$, the $i$-th edge connects vertices $u_i$ and $v_i$.':r'给定一棵树 $T$，有 $N$ 个顶点，编号为 $1,2,\dots,N$。对于 $i=1,2,\dots,N-1$，第 $i$ 条边连接顶点 $u_i$ 与 $v_i$。',
r'Each vertex is painted in a color; vertex $v$ is painted in color $C_v$.':r'每个顶点均涂有一种颜色；顶点 $v$ 的颜色为 $C_v$。',
r'Find the number of integer pairs $(u,v)$ with $1 \leq u < v \leq N$ that satisfy all of the following conditions.':r'求满足 $1 \leq u < v \leq N$ 且符合以下全部条件的整数对 $(u,v)$ 的数量。',
r'Vertices $u$ and $v$ are painted in the same color.':r'顶点 $u$ 与 $v$ 的颜色相同。',
r'The length of the simple path connecting vertices $u$ and $v$ equals the diameter of the tree $T$.':r'连接顶点 $u$ 与 $v$ 的简单路径长度等于树 $T$ 的直径。',
r'Here, the length of a path is the number of edges in it, and the diameter of a tree is the maximum length of a simple path in the tree.':r'路径长度指其中的边数；树的直径指树中简单路径长度的最大值。',
r'The given graph is a tree.':r'给定图为一棵树。',
r'There is $1$ integer pair that satisfies the conditions: $(1,5)$.':r'满足条件的整数对共有 $1$ 个：$(1,5)$。',
r'There are $2$ integer pairs that satisfy the conditions: $(3,6)$ and $(4,7)$.':r'满足条件的整数对共有 $2$ 个：$(3,6)$ 与 $(4,7)$。',
r'There are $2$ integer pairs that satisfy the conditions: $(4,5)$ and $(5,9)$.':r'满足条件的整数对共有 $2$ 个：$(4,5)$ 与 $(5,9)$。',
r'You are given positive integers $N$ and $M$. For each $k = 0, 1, \dots, M-1$, solve the following problem.':r'给定正整数 $N$ 和 $M$。对每个 $k = 0, 1, \dots, M-1$，分别解决以下问题。',
r'Determine whether there exists a positive integer $t$ satisfying the following condition, and if it exists, find the minimum such $t$.':r'判断是否存在满足以下条件的正整数 $t$；若存在，求最小的这种 $t$。',
r'There exists a positive divisor $x$ of $N^t$ such that $x \equiv k \pmod{M}$.':r'$N^t$ 存在一个正约数 $x$，使 $x \equiv k \pmod{M}$。',
r'$N$ and $M$ are integers.':r'$N$ 与 $M$ 均为整数。',
r'Print $M$ lines. The $i$-th line should contain the minimum positive integer $t$ satisfying the condition in the problem statement for $k=i-1$ if such $t$ exists, and $-1$ otherwise.':r'输出 $M$ 行。第 $i$ 行输出 $k=i-1$ 时满足题目条件的最小正整数 $t$；若这种 $t$ 不存在，输出 $-1$。',
r'For example, when $k=3$, $x=3$ is a divisor of $N^1=6$ and satisfies $x\equiv k \pmod{M}$, so the minimum positive integer $t$ satisfying the condition is $t=1$.':r'例如，当 $k=3$ 时，$x=3$ 是 $N^1=6$ 的约数，且满足 $x\equiv k \pmod{M}$，所以满足条件的最小正整数 $t$ 为 $t=1$。',
'All input values are integers.':'所有输入值均为整数。',
'The input is given from Standard Input in the following format:':'输入从标准输入按以下格式给出：',
'Print the answer.':'输出答案。',
'### Problem Statement':'### 题目描述','### Constraints':'### 数据范围','### Input':'### 输入格式','### Output':'### 输出格式',
}

def translate(original):
    text=original
    for source,target in sorted(REPLACE.items(),key=lambda item:-len(item[0])):text=text.replace(source,target)
    text=re.sub(r'Score : (\$[^$]+\$) points',r'分值：\1 分',text)
    text=re.sub(r'### Sample Input (\d+)',r'### 样例输入 \1',text)
    text=re.sub(r'### Sample Output (\d+)',r'### 样例输出 \1',text)
    return text

def main():
    statements=json.loads((CONTENT/'statements.json').read_text('utf8'))
    for row in statements:
        if ':atcoder:' not in row['problem_id']:continue
        value=row['content'];original=value['markdown'];chinese=translate(original)
        value['translation']={'kind':'bundled','provider':'ToBe 中文题面复核','format':TRANSLATION_FORMAT,
          'sourceHash':hashlib.sha256(original.encode()).hexdigest(),'sourceLanguage':'en','targetLanguage':'zh-CN',
          'markdown':chinese,'notice':'中文译文；公式、数值、输入输出与样例保留原题。'}
        assert bundled_translation(value),row['problem_id']
        letter=row['problem_id'].rsplit('::',1)[-1]
        (CONTENT/'abc482/statements'/(letter+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
    (CONTENT/'statements.json').write_text(json.dumps(statements,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('Five Chinese statements passed completeness and immutable-span validation.')

if __name__=='__main__':main()
