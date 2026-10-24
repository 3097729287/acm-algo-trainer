"""Individually authored bridges from problem reasoning to decisive code.

Dry run unless --write is supplied. Reference C++ programs and existing figures
are preserved. This is a set of specific revisions, not a template applied to
unreviewed problems; the separate full-library inventory keeps those pending.
"""
import argparse
import base64
from html import escape
import json
from pathlib import Path
import re
import shutil

from audit_editorial_reasoning import ROOT, SOURCE, reference_programs

SAVE = ROOT / '.backups/editorial-reasoning-20261022'
FIGURES = ROOT / 'docs/editorial-figures'
ECHO = 'remote:nowcoder:141877::D'
REVISED_IDS = {f'remote:nowcoder:141877::{letter}' for letter in 'ABCDEF'}

ECHO_DEFAULT = r'''### 思路

数组 $[1,2,2,1]$ 中，$[1,3]$ 的首尾乘积是 $1\times2=2$，内部和也是 $2$。先想清怎样检验一个区间，再减少枚举次数。

令 $S_i=a_1+\cdots+a_i$，$S_0=0$。内部不含两端，所以其和为 $S_{r-1}-S_l$：从右端点之前的整段，减去左端点及其之前的整段。

![固定右端点三：减掉左端点及其之前，留下内部元素二](assets/editorial-reasoning/echo-interval.svg)

直接枚举 $(l,r)$ 需要平方级时间。固定 $r$，改为猜左端点的**数值** $v=1,\ldots,30$。如果猜对，必有

$$v a_r=S_{r-1}-S_l\quad\Longleftrightarrow\quad S_l=S_{r-1}-v a_r.$$

元素全为正，前缀和严格递增，目标前缀和至多对应一个位置。用 `pos[s]` 反查这个位置，不存在就返回 $-1$。猜数值只是帮我们算出一个候选位置，**还没有保证那个位置的值真是 $v$**。

#### 三个条件为什么足够让答案加一

`wanted` 非负时，查出 `l = pos[wanted]`。依次检查：

- `l >= 1`：查到了真实数组位置。否则没有这个前缀和，连区间左端点都不存在；同时不能访问 `a[-1]`。
- `l <= r - 2`：两个端点之间至少有一个元素，长度至少为三。当前正整数前提下，这是重复确认：它已由 `wanted < S[r-1]` 和前缀和严格递增保证；代码再明确检查一次。
- `a[l] == v`：候选位置的真实值等于刚才的猜测。此时把查表保证的 $S_l=S_{r-1}-v a_r$ 换回去，得到 $a_l a_r=S_{r-1}-S_l$，恰好就是题目的等式。

所以这次 `ans++` 统计的是**刚找到的一个区间 $[l,r]$**，不是统计一个猜测值。`wanted < 0` 时跳过，是因为正整数前缀和不可能为负，且不能访问负下标。

手算 $r=4$ 时，$a_r=1,S_{r-1}=5$：

| 猜测 $v$ | `wanted = 5 - v` | 查表得到 $l$ | 结论 |
|---|---|---|---|
| $1$ | $4$ | $-1$ | 没有这个前缀和，舍去 |
| $2$ | $3$ | $2$ | $a_2=2$，区间 $[2,4]$ 内部和为 $2$，加一 |
| $4$ | $1$ | $1$ | $a_1=1\ne4$；实际首尾乘积 $1$，内部和 $4$，舍去 |
| $5$ | $0$ | $-1$ | $S_0$ 不代表一个数组左端点，舍去 |

每个合法区间都会在 $r$ 为其右端点、$v=a_l$ 时被找到；同一区间的这两个值固定，因此只计一次。本例还会在 $r=3,v=1$ 时计入 $[1,3]$，最终答案为 $2$。

前缀和最多为 $30n$；反查数组初始化、建表和枚举总时间为 $O(30n)$，空间为 $O(30n)$。沿用参考程序的 `long long` 保存答案。

'''

ECHO_DETAILED = r'''### 思路

#### 先用一个真实区间写出要检查的等式

数组是 $[1,2,2,1]$，位置从一开始编号。对区间 $[1,3]$，左端点的数是 $1$，右端点的数是 $2$，内部只有位置二的数 $2$。首尾乘积与内部和都是 $2$，所以这个区间应贡献一次答案。

![固定右端点三：减掉左端点及其之前，留下内部元素二](assets/editorial-reasoning/echo-interval.svg)

前缀和为 $S=[0,1,3,5,6]$。图中 $S_2=1+2$ 包含左端点，减去 $S_1=1$ 才留下内部的 $2$。一般地，内部位置从 $l+1$ 到 $r-1$，所以内部和为

$$S_{r-1}-S_l.$$

减去 $S_{l-1}$ 会留下左端点，使用 $S_r$ 又会把右端点加进来；这两种写法都不是题目要求的内部和。

#### 为什么不枚举左端点位置，而枚举它的值

即使已能常数时间求内部和，枚举所有左右端点仍有平方级候选。题目特别给出了 $1\le a_i\le30$：右端点固定后，我们可以只问三十次“如果左端点的值是 $v$，它应该在哪里”。

`v` 是猜的数值，不是下标。若猜对，合法等式应为

$$v a_r=S_{r-1}-S_l\quad\Longleftrightarrow\quad
S_l=S_{r-1}-v a_r.$$

右边全部已知，记作 `wanted`。它要求的是**左端点所在位置的前缀和**，并不是在数组里直接寻找 `wanted` 这个元素。

每个 $a_i$ 都为正，因此 $S_{i+1}>S_i$；一个前缀和值不可能对应两个不同位置。建表 `pos[S[i]] = i`，初始化为 $-1$。本例中 `pos[1]=1, pos[3]=2, pos[5]=3, pos[6]=4`，其他格子都为 $-1$。只登记真实位置 $1$ 到 $n$，不把 $S_0$ 登记成一个左端点。反查数组长度不超过 $30n+1$。

#### 跟着一次成功的查找走到 `ans++`

固定 $r=3$，右端点的数是 $2$，其之前的前缀和 $S_2=3$。尝试 $v=1$：

1. 计算 `wanted = 3 - 1 * 2 = 1`。
2. `pos[1] = 1`，找到候选左端点 $l=1$；查表已经保证 $S_l=1$。
3. $l\ge1$，候选确实存在；$l\le r-2=1$，区间长度为三。
4. 实际读取 $a_l=a_1=1$，等于刚才猜的 $v=1$。
5. 现在首尾乘积为 $a_1a_3=1\times2=2$，内部和为 $S_2-S_1=3-1=2$，于是区间 $[1,3]$ 贡献一，答案从 $0$ 变为 $1$。

![一次查表如何变成一个真实区间：猜一，目标一，找到左端点一，验算后二等于二](assets/editorial-reasoning/echo-success.svg)

这里无需再写一次“比较乘积与内部和”的条件。查表已经让它们在**猜测值** $v$ 下相等；最后确认真实的 $a_l=v$，才把这个相等关系落实到了实际数组上。

#### 查表命中为什么仍可能是假候选

继续固定 $r=4$。这次 $a_r=1,S_3=5$，所以 `wanted = 5 - v`。

| $v$ | `wanted` | `pos[wanted]` | 核实结果与答案变化 |
|---|---|---|---|
| $1$ | $4$ | $-1$ | 前缀和没有四，不存在候选，答案仍为 $1$ |
| $2$ | $3$ | $2$ | $a_2=2$；$[2,4]$ 首尾 $2\times1=2$，内部 $a_3=2$；答案变为 $2$ |
| $3$ | $2$ | $-1$ | 前缀和没有二，舍去 |
| $4$ | $1$ | $1$ | 找到了位置一，但 $a_1=1\ne4$，舍去 |
| $5$ | $0$ | $-1$ | $S_0=0$ 没有登记成左端点，舍去 |
| $6$ 到 $30$ | 负数 | 不查表 | 不可能对应真实前缀和，直接跳过 |

其中 $v=4$ 最能说明最后一个条件的作用。用**猜的四**确实可以写出 $4\times1=5-1$；但位置一的真实值是**一**，区间 $[1,4]$ 的首尾乘积实际为 $1$，内部和为 $2+2=4$。不检查 `a[l] == v` 就会把这个错误区间计入。

![同一个右端点的两个查表命中：猜二得到合法区间，猜四得到值不符的假候选](assets/editorial-reasoning/echo-candidates.svg)

#### 把每个判断与它保证的事实对应起来

`wanted < 0` 时不能用它访问数组，并且所有真实 $S_l>0$，所以跳过不会漏解。对于非负的目标，因 $v a_r\ge1$，有 `wanted < S[r-1] <= S[n]`，自然不会访问 `pos` 的右侧边界。

`l >= 1` 同时保证命中真实位置、排除未命中的 $-1$，并让后面的 `a[l]` 有效。C++ 的 `&&` 从左向右短路：这个条件失败后，不再求值后面的 `a[l] == v`，所以不会读 `a[-1]`。

`l <= r - 2` 把“至少三个数”直接写进代码。**在本题正整数前提下它是重复确认**：`wanted = S[r-1] - v*a[r] < S[r-1]`，查表成功又意味着 $S_l=\mathrm{wanted}$；前缀和严格递增便推出 $l<r-1$，即 $l\le r-2$。因此不能声称删掉它就会在本题出现长度二的反例。保留它的作用是显式表达长度要求。

`a[l] == v` 将猜测值换成实际值。通过之后，把查表等式移项：

$$S_l=S_{r-1}-v a_r
\ \Longrightarrow\ S_{r-1}-S_l=v a_r=a_l a_r.$$

真实下标、长度条件和题目等式至此全部成立，所以这次 `ans++` 有充分依据。它贡献的是一个区间，不是一个前缀和、一个数值或这个区间里的元素个数。

#### 为什么没有漏掉或重复计算区间

任取一个合法区间 $[l,r]$。外层循环一定访问它的右端点；内层也一定尝试 $v=a_l$，因为 $a_l\in[1,30]$。合法等式保证算出的 `wanted` 恰好是 $S_l$，严格递增保证反查找回的就是这个 $l$，三个判断全部通过，所以不会遗漏。

反过来，一次通过检查就只确定了一个区间。同一区间只能在固定的 $r$ 和固定的 $v=a_l$ 时被计入；另一个 $v$ 即便查到同一位置，也不能再满足 `a[l] == v`，所以不会重复。

本例最终只有 $[1,3]$ 与 $[2,4]$ 两个合法区间，答案为 $2$。全枚举检查全部区间也得到同一结果；这个小例用来核对过程，而上面两段负责说明任意输入的正确性。

每个右端点尝试三十次。前缀和至多为 $30n$，反查数组初始化也计入成本，故时间、空间均为 $O(30n)$。沿用参考程序的 `long long` 保存答案。若允许零或负数，前缀和可能重复或不再递增，“一个前缀和值只保存一个位置”的论证就不再成立，需要重新设计算法。

'''

CORRIDOR_DEFAULT = r'''#### 一次答案累加对应一条原区间

上图取 $p=2$。A 为 $[1,3]$，两端覆盖数分别为 $2,4$，差的绝对值为 $2$，所以 A 贡献一；D 为 $[3,5]$，两端均被四个区间覆盖，差为零，贡献零；H 为 $[7,9]$，覆盖数为 $4,1$，差为三，仍只贡献一。

因此 `ans += abs(cover(l) - cover(r)) >= p` 加入的是比较结果：成立转成整数一，不成立转成零。题目数的是区间条数，不能把差值本身加进答案。循环遍历 `seg` 中的每条原记录一次；覆盖公式已经求对端点值，比较又正是题目的要求，所以每次累加都对应一个合格区间，不会遗漏或重复。重复区间是不同记录，各自贡献一次。

'''

CORRIDOR_DETAILED = r'''#### 一次答案累加对应一条原区间

覆盖公式只是完成了“给定位置，求覆盖数”的子问题，最后还要回到题目要求的计数对象：一条条**原区间记录**。

将上图八个区间作为完整输入，设 $p=2$，逐条执行最后一层循环：

| 原记录 | 区间 | 左端覆盖数 | 右端覆盖数 | 差的绝对值 | 是否加一 |
|---|---|---|---|---|---|
| A | $[1,3]$ | $2$ | $4$ | $2$ | 是 |
| B | $[2,4]$ | $3$ | $4$ | $1$ | 否 |
| C | $[1,7]$ | $2$ | $4$ | $2$ | 是 |
| D | $[3,5]$ | $4$ | $4$ | $0$ | 否 |
| E | $[4,8]$ | $4$ | $3$ | $1$ | 否 |
| F | $[5,6]$ | $4$ | $4$ | $0$ | 否 |
| G | $[6,8]$ | $4$ | $3$ | $1$ | 否 |
| H | $[7,9]$ | $4$ | $1$ | $3$ | 是 |

答案为三，因为恰有 A、C、H 三条记录达标。A 的差是二、H 的差是三，但它们都只贡献**一条区间**。

这正是 `ans += abs(cover(l) - cover(r)) >= p` 的含义：先调用两次 `cover`，求差再取绝对值，最后与阈值比较；比较结果为 `true` 或 `false`，参与整数相加时分别为一或零。因此累计的是达标记录的数量，每条至多贡献一。

充分性来自前面已证明的覆盖公式：两次查询返回真实的 $d(l_i),d(r_i)$，比较通过就满足原题条件。完备性与唯一性来自循环对象：`seg` 保留所有原始区间记录，每条恰好访问一次。排序后的端点数组只负责查询；如果改为把它们按下标重新配成区间，就不再是在检查原题对象。即使两条记录坐标相同，也必须分别检查。$p=0$ 时每条记录的差都不小于零，答案自然等于 $n$。

'''

TIME_DEFAULT = r'''#### 为什么可以从“到达终点”判断这个上限可行

考虑四个点组成的环 $1-2-3-4-1$，塔在一、三，起点是二，终点是四。两次 BFS 得到的时差依次为 $[2,0,2,0]$。虽然起终点时差都为零，从二到四仍必须经过一或三，途中最大时差至少为二。

![四点环按时差上限筛点：上限一时起终点隔开，上限二时出现合法路径](assets/editorial-reasoning/time-threshold.svg)

`!seen[v]` 表示这个点尚未安排访问，防止在无向边上反复往返；`w[v] <= limit` 表示它允许进入。起点先通过同样的权值检查，此后每个入队的点都由一个合法点沿边到达，所以入队就保证存在一条全程不超限的起点到它的路径。弹出终点时可以立即返回 `true`；队列耗尽仍未到终点则没有这条路径。

图中上限一不可行、上限二可行，上限再增大也保留原路径。因此二分中，可行就保留含 `mid` 的左半段，不可行就排除所有不大于 `mid` 的值。最后留下的正是最小可行上限，而不是任意一次检查找到的上限。

'''

TIME_DETAILED = r'''#### 为什么可以从“到达终点”判断这个上限可行

端点时差只是答案的下界，途中还可能有更大的点权。考虑四点环，边为 $(1,2),(2,3),(3,4),(4,1)$；塔为一、三，起点二、终点四。距离与时差为：

| 点 | 到塔一的距离 | 到塔三的距离 | 两距离之差的绝对值 |
|---|---|---|---|
| $1$ | $0$ | $2$ | $2$ |
| $2$，起点 | $1$ | $1$ | $0$ |
| $3$ | $2$ | $0$ | $2$ |
| $4$，终点 | $1$ | $1$ | $0$ |

![四点环按时差上限筛点：上限一时起终点隔开，上限二时出现合法路径](assets/editorial-reasoning/time-threshold.svg)

若上限为一，二、四都允许经过，却没有边连接它们；连接两边的点一、三都超限，所以不可行。上限为二时，路径 $2\to1\to4$ 的点权为 $0,2,0$，最大值二，检查成功。时差为零的终点不能抵消途中时差二。

把代码的三个提前判断分开看：

- `w[s] > limit`：任何路径都包含起点，起点超限便无解，不应先把它入队。
- `!seen[v] && w[v] <= limit`：后半句是路径的合法性约束；前半句避免一个点重复入队。点一经入队就设置 `seen`，不用等到出队，否则两个父节点可能重复安排它。
- `u == t`：现在发现了一条符合上限的完整路径，可以返回可行；不需要等所有点访问完。

这些判断之所以充分，有一个贯穿搜索的事实：**每个已经入队的点，都有一条从起点出发、全程点权不超过上限的路径。**起点检查保证它一开始成立。若它对当前点 $u$ 成立，而边 $(u,v)$ 的新点 $v$ 也不过限，就把这条路径再延长一条边，事实仍成立。因此到达终点不是凭一个布尔标记猜答案，而是已经得到这类路径存在的证据。

反过来，若有一条允许路径，沿着这条路径看第一个没被访问的点；它之前的点已被访问，搜索处理那条边时就应当把它加入队列，形成矛盾。所以队列耗尽而终点未到达，确实意味着不存在允许路径。按第一次入队的父边回溯，得到的路径不重复顶点，也满足题目的简单路径要求。这里每个点只关心能否到达，不需要为它记录多个“更优时差”：时差是提前固定的点权，整个检查过程只验证连通性。

#### 二分更新究竟排除了哪些答案

若上限 $D$ 可行，那么同一条路径对所有更大的上限都可行；若 $D$ 不可行，更小的上限删点更多，也都不可行。可行性只有“若干不可行，随后全可行”这一种顺序。

`lo=max(w[s],w[t])` 是必要下界，`hi=n-1` 一定可行，因为原图连通且最短距离不超过 $n-1$。二分保留真实最小答案所在的闭区间 $[lo,hi]$：

- `possible(mid)` 成功，最小可行值不超过 `mid`，所以 `hi=mid`；`mid` 本身可能就是答案，不能删掉。
- 失败时，所有不大于 `mid` 的值均不可行，所以 `lo=mid+1`。

四点环中，初始为 $[0,3]$。先检查一，失败后变为 $[2,3]$；再检查二，成功后变为 $[2,2]$，输出二。两种更新都使区间缩小，又不丢失最小可行值，故相遇时的值恰为答案。若起点等于终点，上述路径可以只有一个点，但仍须包含该点的权值。

'''

ORDERS_DEFAULT = r'''#### 为什么两份最小费用相加，就能决定更新答案

取 $n=7$，第一批费用为 $a=[1,9,2,9,9,9,9]$，第二批为 $b=[9,9,9,9,2,9,1]$，预算六。留空位置四，前缀 $[1,3]$ 选两份的最小费用为 $a_1+a_3=3$，后缀 $[5,7]$ 选两份的最小费用为 $b_5+b_7=3$。

![两批订单留空位置四：左选一和三，右选五和七，最小总费用三加三等于六](assets/editorial-reasoning/orders-split.svg)

固定空位后，左右使用的位置完全分开，且最近的两端也隔着空位，所以两边的最低费用方案能够同时选用。任何同样分割、同样份数的方案又都不可能比各自的最小费用更便宜。因此检查的和，恰好是这一分割下选两批各 $k$ 份的**真实最小总费用**，不只是一个估计。

于是和不超过预算就确实存在完整方案，`ans=k` 有依据；和超过预算，则这一分割下其他选法只会更贵。枚举所有空位覆盖所有合法方案，取最大的可行 $k$ 即得答案。例中预算六可以取二；预算五时，这四份唯一可能的位置 $1,3,5,7$ 费用仍为六，取二不可行，但选第一批位置一、第二批位置七只花二，可以取一。

'''

ORDERS_DETAILED = r'''#### 为什么两份最小费用相加，就能决定更新答案

取 $n=7$，第一批费用 $a=[1,9,2,9,9,9,9]$，第二批费用 $b=[9,9,9,9,2,9,1]$，预算六。把位置四留空，左边考虑位置一到三，右边考虑位置五到七：

![两批订单留空位置四：左选一和三，右选五和七，最小总费用三加三等于六](assets/editorial-reasoning/orders-split.svg)

`pref[3][2]` 不是保存“某两份订单的费用”，而是回答一个完整的小问题：**只在位置一到三中，互不相邻地选恰好两份，最低要付多少。**此时只有选一、三，故为三。`Q[5][2]` 回答右侧位置五到七的同类问题，最低费用也是三。两张表存的是可达到的最低值；无法选足份数时存无穷大，不是零。

固定这个空位后，两边的选择没有共享位置，跨批次也不会相邻。因此取得左侧最低费用的方案与取得右侧最低费用的方案可以**同时实现**，费用为 $3+3=6$。反过来，任意两边各选两份的方案，左右费用都不小于各自表中的值，所以总费用不小于六。上下两个方向合起来，证明表中两项的和恰为这一个分割的真实最小费用。

这就解释了 `pref[i-2][k] + cur[k] <= budget` 的充分性：它比较的是一个确实能实现的完整方案的最低费用，比较通过就可以把 `ans` 更新为 $k$。若比较失败，则这个分割下的任意同份数方案都会超预算。循环枚举所有分割，而任意合法方案的两批之间必有空位，所以不会遗漏。我们取最大份数，不是在统计方案数，同一个方案被多个空位容纳也不影响结果。

例中选 $1,3,5,7$ 最少需要六，故预算六的答案为二；预算五不能选二。四份互不相邻的位置在长度七中只能是 $1,3,5,7$，而选第一批一、第二批七仅花二，所以预算五的答案为一。这也核对了“不可行不能当成零费用”的初始化规则。

#### 最小值转移里的两项为什么穷尽所有方案

对 `pref[j][k]` 的任何合法方案，位置 $j$ 只有“不选”和“选”两种情况。前者正好属于 `pref[j-1][k]`；后者去掉 $j$ 后，前面只能在 $[1,j-2]$ 再选 $k-1$ 份，费用再加 $a_j$。两类互不混淆且覆盖所有方案，取两类最低费用的较小值，就得到整个问题的最低费用。

例如算 `pref[3][2]`：不选三，则在前两个相邻位置中无法选足两份，第一项为无穷大；选三，则前面只能在位置一选一份，第二项为 $1+2=3$。所以结果是三，而不是直接从 $a$ 数组拿两个最小值。后缀转移按同样的分类向右看，选择当前位置后必须跳过紧邻的下一位置。

#### 滚动数组在这一轮分别代表哪一行

准备计算 $i=5$ 时，`next` 是 $Q[6]$，`next2` 是 $Q[7]$，`cur` 才是这次要写入的 $Q[5]$：

![计算后缀第五行时的完整操作数与交换后的版本：第六行、第七行只读，第五行新写](assets/editorial-reasoning/orders-rolling.svg)

本例有 $Q[6][2]=\infty$，因为六、七相邻，不能选两份；$Q[7][1]=1$。选择位置五时再取右侧位置七的一份，因此

$$Q[5][2]=\min\bigl(Q[6][2],Q[7][1]+b_5\bigr)
=\min(\infty,1+2)=3.$$

此时先用 `cur[2]=3` 与 `pref[3][2]=3` 检查预算，然后才交换。`next2.swap(next)` 使 `next2` 保存刚才的 $Q[6]$；`next.swap(cur)` 使 `next` 保存刚算好的 $Q[5]$。下一轮 $i=4$ 正好需要这两行。`cur` 中的旧缓冲值会在下一轮各个 $k$ 被重新赋值，不会作为当前来源读取。

内层从 `ans+1` 开始，是因为不超过已知答案的份数无法改善最大值，并不是假定费用随份数单调。若某次失败仍继续尝试更大 $k$，代码没有依赖未经证明的提前退出。

'''

APPENDICES = {
    'remote:nowcoder:141877::A': (r'''#### 这一行更新为什么对应题目的动作

从 $x=0$ 开始读 $[1,0,3]$：一是奇数，变为 $-1$；零是偶数，变回零；三是奇数，最后为 $-1$。

`a % 2 == 0` 检查当前读入的数能否被二整除；成立时取增量一，否则取增量负一，再加到 `x` 上。每一步的增量正好等于题目规定的动作，所以处理前几个数之后，`x` 始终是这些动作执行后的真实值；处理完全部数时直接输出即可。选择增量时读取的是 `a`，当前 `x` 是否为奇数不影响动作。

''',r'''#### 这一行更新为什么对应题目的动作

把 `x += (a % 2 == 0 ? 1 : -1)` 分为两步读：先由当前输入 `a` 决定本次增量，再把增量加到状态 `x`。问号前条件成立时使用问号后的第一项一，不成立时使用冒号后的负一；它只选择一个增量，不会同时执行加一和减一。

以原来的 $[1,0,3]$ 为例，三次增量依次为 $-1,+1,-1$，累积状态为 $0,-1,0,-1$。动作顺序与输入顺序一致；零能被二整除，因此也走加一的分支。

初始状态就是输入的 $x$。假设前 $i-1$ 次更新已与规则一致，第 $i$ 次选择同样的增量，更新后自然仍一致。由此直到第 $n$ 次都保持一致，输出的便是最终计数器。处理过程中无需保存过去的元素，也无需按 `x` 的奇偶性重新分支。

'''),
    'remote:nowcoder:141877::B': (r'''#### 用实际金额核对商和余数

例如十枚金币由三人均摊，一枚等于一百粒碎银。总价先换成一千粒，每人舍去不足一粒的部分后付三百三十三粒；三百三十三又等于三枚金币加三十三粒碎银，所以输出 `3 33`。

先换成碎银再除人数，才只会舍去题目允许舍去的小于一粒的部分。最后 `pay / unit` 是能凑出的整枚金币，`pay % unit` 是凑完后剩下的碎银；两者满足 `金币数 * unit + 碎银数 == pay`，不会丢掉已经计入付款的金额。先算 `a / b` 则会丢掉不足一枚金币的部分，例如这个例子每人会少付三十三粒。

''',r'''#### 用实际金额核对商和余数

参考程序先把费用换成最小单位，得到整数 `pay`。此时每个人已经完成“不足一粒碎银舍去”的规则，后面只是换一种方式表示同一笔钱。

整数除法给出唯一的 $q,r$，满足 $\mathrm{pay}=q\cdot\mathrm{unit}+r$，且 $0\le r<\mathrm{unit}$。所以 `pay / unit` 的商恰是能换成的完整金币数量，`pay % unit` 的余数恰是剩余碎银。前面的例子中 $333=3\times100+33$，三十三不足一枚金币，表示方式符合输出要求。

这两次除法作用不同：除人数会按题意舍去不足一粒的费用，除换算单位则借助余数完整保留金额。正整数范围下，整数除法直接给出所需的向下取整结果，避免浮点表示影响最后一粒碎银。

'''),
    'remote:nowcoder:141877::C': (CORRIDOR_DEFAULT, CORRIDOR_DETAILED),
    'remote:nowcoder:141877::E': (TIME_DEFAULT, TIME_DETAILED),
    'remote:nowcoder:141877::F': (ORDERS_DEFAULT, ORDERS_DETAILED),
}


def svg(title, width, height, elements):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="' + str(width) + '" height="' + str(height)
            + '" viewBox="0 0 ' + str(width) + ' ' + str(height) + '" role="img">'
            + '<title>' + escape(title) + '</title><rect width="100%" height="100%" rx="12" fill="#fff"/>'
            + '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" fill="#20334a">'
            + ''.join(elements) + '</g></svg>')


def text(x, y, value, size=22, color='#20334a', anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>'


def box(x, y, w, h, fill='#eff6ff', stroke='#2d6db4'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def echo_figures():
    e = [text(26, 40, '内部只取两端之间：a = [1, 2, 2, 1]', 24)]
    for i, value in enumerate([1, 2, 2, 1], 1):
        x = 72 + (i-1)*130
        fill, stroke = ('#dcfce7', '#087b48') if i == 2 else (('#dbeafe', '#2d6db4') if i <= 3 else ('#f1f5f9', '#8995a5'))
        e += [text(x+54, 82, '位置 '+str(i), 18, anchor='middle'), box(x, 96, 108, 62, fill, stroke), text(x+54, 135, str(value), 28, anchor='middle')]
    e += [text(126, 190, '左端 l=1', 19, anchor='middle'), text(256, 190, '内部', 19, '#087b48', 'middle'), text(386, 190, '右端 r=3', 19, anchor='middle'),
          text(30, 239, 'S₂ = 1 + 2 = 3   （到右端点之前为止）', 21),
          text(30, 277, '减 S₁ = 1          （左端点也一并减掉）', 21),
          box(26, 298, 568, 60, '#ecfdf5', '#087b48'), text(44, 337, '内部和 3 − 1 = 2 ；首尾乘积 1 × 2 = 2', 21, '#06613b')]
    interval = svg('内部和等于右端点之前的前缀减去包含左端点的前缀', 620, 382, e)
    e = [text(26, 40, '固定 r=3：一次成功的查找', 24)]
    steps = [('① 猜左端点的值 v=1', '此时右端点 a₃=2，S₂=3'),
             ('② 算 wanted = 3 − 1×2 = 1', '它是要求的前缀和值，不是元素值'),
             ('③ 查 pos[1] = 1，得到 l=1', '真实位置存在，区间 [1,3] 长度为三'),
             ('④ 验证 a₁=1，等于猜测 v', '首尾 1×2 = 内部 3−1 = 2'),
             ('⑤ 计入区间 [1,3]', 'ans：0 → 1')]
    for index, (line, detail) in enumerate(steps):
        y = 66 + index*108
        e += [box(26, y, 568, 86, '#ecfdf5' if index == 4 else '#f0f6ff', '#087b48' if index == 4 else '#2d6db4'), text(44, y+32, line, 21), text(44, y+65, detail, 18)]
    success = svg('猜值、算前缀、反查位置、核实真实值、计入一个区间的五步', 620, 618, e)
    e = [text(26, 40, '固定 r=4：查表命中，还要检查真实值', 23), text(26, 78, 'a = [1,2,2,1]；S₃=5，a₄=1', 21)]
    cases = [(110, '猜 v=2 → wanted=3 → l=2', '[2,4]：左端实际值 a₂=2，猜对', '首尾 2×1=2；内部 a₃=2 → 加一', True),
             (274, '猜 v=4 → wanted=1 → l=1', '[1,4]：左端实际值 a₁=1，猜错', '首尾 1×1=1；内部 2+2=4 → 舍去', False)]
    for y, line, detail, result, accepted in cases:
        color, fill = ('#087b48', '#ecfdf5') if accepted else ('#a32e36', '#fff1f2')
        e += [box(26, y, 568, 140, fill, color), text(44, y+35, line, 21), text(44, y+76, detail, 21), text(44, y+115, result, 20, color)]
    e += [text(26, 458, '命中只说明“用猜的 v 解方程能成立”。', 21), text(26, 495, 'a[l] == v 才说明它对应真实数组。', 21)]
    return {'echo-interval.svg': interval, 'echo-success.svg': success,
            'echo-candidates.svg': svg('两个反查命中的比较：值相符的合法候选与值不符的错误候选', 620, 526, e)}


def time_figures():
    e = [text(26, 38, '四点环：塔在 1、3；起点 2，终点 4', 23)]
    for top, limit in [(66, 1), (352, 2)]:
        e += [text(26, top+24, f'上限 D={limit}：'+('仅允许两个孤立点，不能到达' if limit == 1 else '允许经过塔点，出现完整路径'), 21)]
        positions = {1:(300, top+68), 2:(164, top+144), 3:(300, top+220), 4:(436, top+144)}
        for left, right in [(1, 2), (2, 3), (3, 4), (4, 1)]:
            x1,y1=positions[left];x2,y2=positions[right]
            color = '#087b48' if limit == 2 and (left,right) in [(1,2),(4,1)] else '#a0aab7'
            e.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="4"'+(' stroke-dasharray="7 5"' if limit == 1 else '')+'/>')
        for node, (x,y) in positions.items():
            allowed = limit == 2 or node in [2,4]
            e += [f'<circle cx="{x}" cy="{y}" r="26" fill="'+('#dcfce7' if allowed else '#f1f5f9')+'" stroke="'+('#087b48' if allowed else '#8995a5')+'" stroke-width="2"/>', text(x,y+8,str(node),22,anchor='middle')]
            if node in [1,3]:
                e.append(text(x+40,y+7,('塔 A' if node == 1 else '塔 B')+'，w=2',19))
            else:
                e.append(text(x,y+49,('s' if node == 2 else 't')+'，w=0',19,anchor='middle'))
    e += [text(26, 653, '绿色点：允许；灰色点：超限；下图绿边：路径 2→1→4', 18), text(26, 688, '端点时差都是 0，途中最大时差仍为 2。', 21)]
    return {'time-threshold.svg': svg('四点环随时差上限放开的允许子图：一不可行，二可行', 620, 716, e)}


def orders_figures():
    e = [text(26, 40, '两批各选 2 份：中间位置 4 必须留空', 23)]
    for i in range(1,8):
        x=29+(i-1)*82
        chosen = i in [1,3,5,7]
        color = '#2d6db4' if i in [1,3] else '#087b48' if i in [5,7] else '#8995a5'
        fill = '#dbeafe' if i in [1,3] else '#dcfce7' if i in [5,7] else '#f1f5f9'
        e += [text(x+34,83,'编号 '+str(i),17,anchor='middle'),box(x,99,68,64,fill,color),text(x+34,138,str(i),25,anchor='middle')]
        label = ('a='+str({1:1,3:2}[i])) if i in [1,3] else ('b='+str({5:2,7:1}[i])) if i in [5,7] else '留空' if i == 4 else '不选'
        e.append(text(x+34,195,label,19,color,'middle'))
    e += [text(26,247,'左侧 [1,3]：P[3][2] = a₁+a₃ = 1+2 = 3',21,'#2d6db4'), text(26,289,'右侧 [5,7]：Q[5][2] = b₅+b₇ = 2+1 = 3',21,'#087b48'), box(26,315,568,58,'#ecfdf5','#087b48'),text(44,353,'两边可同时选择：最小总费用 3+3=6',22,'#06613b')]
    split=svg('互不相邻的两批订单在空位四处分割，左侧最小费用三右侧最小费用三',620,399,e)
    e=[text(26,40,'计算 i=5 之前：来源行只读，cur 新写',23),text(26,84,'选中份数',20)]
    for x,k in [(380,0),(460,1),(540,2)]:
        e.append(text(x,84,'k='+str(k),18,anchor='middle'))
    for y,label,values in [(108,'next  = Q[6]','0     1     ∞'),(185,'next2 = Q[7]','0     1     ∞'),(365,'cur   = Q[5]','0     1     3')]:
        e += [box(26,y,568,58,'#ecfdf5' if y==365 else '#eff6ff','#087b48' if y==365 else '#2d6db4'),text(44,y+37,label,23)]
        for x,value in zip([380,460,540],values.split()):
            e.append(text(x,y+37,value,23,anchor='middle'))
    e += [text(26,284,'不选位置 5：next[2] = ∞',21),text(26,324,'选位置 5：next2[1] + b₅ = 1+2 = 3',21),text(26,460,'交换后进入 i=4：next=Q[5]，next2=Q[6]',20),text(26,500,'预算检查在交换前：pref[3][2]+cur[2] = 3+3',20)]
    return {'orders-split.svg':split,'orders-rolling.svg':svg('后缀DP第五行由第六行与第七行的旧值计算，显示完整操作数和交换顺序',620,528,e)}


def replace_reasoning(markdown, replacement):
    pattern = r'^### 思路\s*\n.*?(?=^### 参考代码\s*$)'
    revised, count = re.subn(pattern, lambda _: replacement, markdown, count=1, flags=re.S | re.M)
    if count != 1:
        raise ValueError('Expected one main reasoning section')
    return revised


def append_reasoning(markdown, addition):
    heading=addition.splitlines()[0]
    markdown=re.sub(r'^'+re.escape(heading)+r'\n.*?(?=^### 参考代码\s*$)', '', markdown, count=1, flags=re.M|re.S)
    index=markdown.index('### 参考代码')
    return markdown[:index].rstrip()+'\n\n'+addition+markdown[index:]


def backup(path):
    target = SAVE / 'before' / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    figure_groups = {ECHO:echo_figures(), 'remote:nowcoder:141877::E':time_figures(), 'remote:nowcoder:141877::F':orders_figures()}
    figures = {name:content for group in figure_groups.values() for name,content in group.items()}
    revised_count = 0
    staged = {}
    for variant in ['solutions', 'detailed_solutions']:
        path = SOURCE / (variant + '.json')
        rows = json.loads(path.read_text(encoding='utf-8'))
        for row in rows:
            identity=row['problem_id']
            if identity not in REVISED_IDS:
                continue
            old = row['markdown']
            row['markdown'] = (replace_reasoning(old, ECHO_DEFAULT if variant == 'solutions' else ECHO_DETAILED) if identity==ECHO else append_reasoning(old,APPENDICES[identity][variant=='detailed_solutions']))
            assert reference_programs(old) == reference_programs(row['markdown']), 'Verified reference program changed'
            for name, content in figure_groups.get(identity,{}).items():
                # Keep every old image, including the reusable prefix lesson.
                row['images']['assets/editorial-reasoning/' + name] = 'data:image/svg+xml;base64,' + base64.b64encode(content.encode('utf-8')).decode('ascii')
            revised_count += old != row['markdown']
        staged[path] = rows
    if args.write:
        for path, rows in staged.items():
            backup(path)
            path.write_text(json.dumps(rows, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
        FIGURES.mkdir(parents=True, exist_ok=True)
        for name, content in figures.items():
            target = FIGURES / name
            if target.exists():
                backup(target)
            target.write_text(content, encoding='utf-8')
        meta_path = SOURCE / 'meta.json'
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        if meta.get('editorialReasoningRevision') != '2026-10-22-nowcoder141877-v1':
            backup(meta_path)
            meta['editorialReasoningRevision'] = '2026-10-22-nowcoder141877-v1'
            meta['revision'] = str(int(meta.get('revision', '0')) + 1)
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'authoredProblems': sorted(REVISED_IDS), 'changedArticles': revised_count,
                      'specificFigures': len(figures), 'dryRun': not args.write,
                      'referenceProgramsChanged': 0, 'otherArticlesRewritten': 0}, indent=2))


if __name__ == '__main__':
    main()
