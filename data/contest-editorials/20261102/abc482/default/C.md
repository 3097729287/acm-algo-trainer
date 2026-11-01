## C. Band Count

### 题意

[原题链接](https://atcoder.jp/contests/abc482/tasks/abc482_c)

$H\times W$ 网格上放有 $N$ 枚棋子，每枚的位置不同。回答 $Q$ 次查询：统计行号在 $[u,d]$ 内的棋子数，或列号在 $[l,r]$ 内的棋子数。$H,W\le10^9$，$N,Q\le3\times10^5$。

### 从零讲：lower_bound 与 upper_bound：从位置到数量

<details>
<summary>展开可复用的基础知识</summary>

#### lower_bound 与 upper_bound：从位置到数量

#### 什么时候使用

有一批可以比较大小的数据，需要反复问“小于某数的有几个”“某个值出现几次”“第一个达到要求的元素在哪”。先排序，再查边界，能避免每次从头扫描。这里先讨论从小到大的 $\verb@vector<int>@$，头文件为 $\verb@<algorithm>@$ 和 $\verb@<vector>@$，适用于 C++17。

#### 先弄清返回的是什么

$\verb@a.begin()@$ 指向第一个元素，$\verb@a.end()@$ 指向末元素之后的空位置。$\verb@[a.begin(), a.end())@$ 包含左端、不包含右端。迭代器可以理解为指向容器中某个位置的标记；它不是元素的值，也不是数量。

设有序数组为 $[1,2,2,2,5,8]$，下标从零开始，查询 $x=2$：

![相等元素位于两条边界之间，边界位置之前的格子数就是计数](assets/foundation-bounds-bounds.svg)

- $\verb@lower_bound(a.begin(), a.end(), x)@$ 返回第一个**大于等于** $\verb@x@$ 的位置，这里是下标一。
- $\verb@upper_bound(a.begin(), a.end(), x)@$ 返回第一个**严格大于** $\verb@x@$ 的位置，这里是下标四。

把名字与等号绑定记忆：$\verb@lower_bound@$ 是相等区间的左边界，$\verb@upper_bound@$ 是相等区间的右边界；没有相等元素时两条边界重合。两个函数均不保证命中 $\verb@x@$。

```cxx
vector<int> a{1, 2, 2, 2, 5, 8};
int x = 2;
auto lo = lower_bound(a.begin(), a.end(), x);
auto hi = upper_bound(a.begin(), a.end(), x);
int less = int(lo - a.begin());          // 1 个元素 < 2
int lessEqual = int(hi - a.begin());     // 4 个元素 <= 2
int equal = int(hi - lo);                // 3 个元素 == 2
```

#### 为什么“位置减 begin”可以计数

$\verb@lo@$ 之前恰有下标 $0$ 到 $0$ 的一个元素。一般地，第一个大于等于 $x$ 的位置如果是 $k$，它前面的下标为 $0,1,\ldots,k-1$，恰有 $k$ 个；有序性保证这 $k$ 个全部严格小于 $x$，之后没有漏下的小数。对 $\verb@vector@$，$\verb@lo-a.begin()@$ 就是跨过的格子数 $k$。

同理，$\verb@hi@$ 之前全部不大于 $x$，所以它的下标就是不大于 $x$ 的数量。令数组长度为 $n$，便有：

| 要统计的元素 | C++ 表达式 | 本例结果 |
|---|---|---|
| 小于 $x$ | $\verb@lo - a.begin()@$ | $1$ |
| 不大于 $x$ | $\verb@hi - a.begin()@$ | $4$ |
| 大于等于 $x$ | $\verb@a.end() - lo@$ | $5$ |
| 大于 $x$ | $\verb@a.end() - hi@$ | $2$ |
| 等于 $x$ | $\verb@hi - lo@$ | $3$ |

因此，函数本身找的是分界位置，计数来自分界两边的长度。查询闭区间 $[L,R]$ 中的数量（保证 $L\le R$），用 $\verb@upper_bound(..., R)-lower_bound(..., L)@$；这也避免了写 $\verb@L-1@$ 时可能发生的整数下溢。

#### 底层怎样二分

下面返回下标，展示 $\verb@lower_bound@$ 的核心逻辑，不依赖库函数：

```cxx
int first_ge(const vector<int>& a, int x) {
    int left = 0, right = int(a.size());
    // 答案在位置 [left, right] 内；待判断元素在 [left, right)。
    while (left < right) {
        int mid = left + (right - left) / 2;
        if (a[mid] < x) left = mid + 1;
        else right = mid;
    }
    return left;  // 可以等于 a.size()，表示没有符合条件的元素
}
```

若中点小于 $x$，它左侧都小于 $x$，连同中点一起排除；否则答案不会在中点右侧，把右边界移到中点，保留中点本身作为可能答案。每次排除约一半候选，区间长度从 $n$ 变成约 $n/2,n/4,\ldots$，经过约 $\log_2 n$ 次就剩一个边界，所以时间为 $O(\log n)$，额外空间为 $O(1)$。

实现 $\verb@upper_bound@$ 时，把 $\verb@a[mid] < x@$ 改为 $\verb@a[mid] <= x@$：遇到相等也继续向右，才能越过全部重复值。比如六个数查二，$\verb@lower_bound@$ 的左边界、右边界和中点三个下标依次为 $(0,6,3)$、$(0,3,1)$、$(0,1,0)$，最终返回一；$\verb@upper_bound@$ 依次为 $(0,6,3)$、$(4,6,5)$、$(4,5,4)$，最终返回四。

#### 使用条件和边界

第一次排序花 $O(n\log n)$，之后 $q$ 次查询共花 $O(q\log n)$。每次查询前都重新排序，会丢掉复用有序数组的优势。若还需要原来的配对、编号或顺序，应另存原数据，再排序供查询的副本。

查零时两条边界都在 $\verb@begin()@$；查十时都在 $\verb@end()@$；查三时都指向五。空数组也会返回 $\verb@end()@$，计数自然为零。**可以拿 $\verb@end()@$ 计算长度，不能解引用它。** 查是否存在应写 $\verb@it != a.end() && *it == x@$。

一般前提是比较条件能把范围分成两段；完整升序是最易保证的方式。普通乱序数组不能直接套用。降序或自定义排序必须使用匹配的比较器，不能沿用上表的自然大小解释。

$\verb@vector@$、数组的随机访问迭代器支持常数时间跳到中点和相减，所以总时间为 $O(\log n)$。$\verb@list@$ 或 $\verb@set@$ 的迭代器不支持相减，通用二分虽然比较次数是对数，迭代器移动却可能达到线性；在 $\verb@set@$、$\verb@map@$ 上优先用成员函数 $\verb@s.lower_bound(x)@$、$\verb@s.upper_bound(x)@$，它们沿树查找为 $O(\log n)$。成员函数得到的迭代器到 $\verb@begin()@$ 的距离仍未必能快速计算。

规范核对：[C++ 工作草案：二分边界算法](https://eel.is/c++draft/alg.binary.search)。本文只使用 C++17 已有接口。


</details>

### 从零讲：vector：长度可变的连续数组

<details>
<summary>展开可复用的基础知识</summary>

#### vector：长度可变的连续数组

$\verb@vector<T>@$ 保存一串同类型的元素，适合按下标访问、扫描、排序。$\verb@T@$ 是元素类型，例如 $\verb@vector<int>@$ 保存整数，$\verb@vector<pair<int,int>>@$ 保存整数对，$\verb@vector<vector<int>>@$ 可保存每个顶点各自的邻居。需要 $\verb@<vector>@$。

```cxx
vector<int> a(3, 7);   // 三个元素，内容是 7、7、7
a.push_back(9);       // 在末尾追加，现在长度为 4
int x = a[1];         // 从 0 编号，这里得到 7
a[1] = 2;            // 改第二个元素
int n = int(a.size());
```

$\verb@vector<int> a(3)@$ 创建三个值为零的元素；$\verb@a.reserve(3)@$ 只预留容量，元素数仍为零，此时不能访问 $\verb@a[0]@$。长度 $\verb@size()@$ 与容量 $\verb@capacity()@$ 是不同概念。

下标访问为 $O(1)$，遍历为 $O(n)$。末尾追加通常为 $O(1)$；容量不足时会分配更大的连续空间并搬移元素，这次可能为 $O(n)$，一连串追加的平均成本称为摊还 $O(1)$。中间插入或删除会搬移后续元素，最坏 $O(n)$。内存是元素量的 $O(n)$，并可能预留部分尚未使用的容量。

$\verb@begin()@$ 指向首元素，$\verb@end()@$ 指向尾后位置，$\verb@sort(a.begin(),a.end())@$ 操作整个数组。$\verb@a[i]@$ 不检查越界；下标须满足 $0\le i<\mathrm{size}$。$\verb@at(i)@$ 会检查越界并抛异常。空数组不能访问 $\verb@front()@$、$\verb@back()@$；$\verb@pop_back()@$ 也要求非空。

扩容后指向旧存储的迭代器、引用和指针会失效。遍历的同时 $\verb@push_back@$，不能假定此前取得的引用仍可用。读取大数组的函数常用 $\verb@const vector<int>& a@$ 按常量引用传入，既不复制也禁止通过该引用修改；$\verb@vector<int> a@$ 按值传参则复制内容。选择副本还是引用取决于是否要保留独立数据。


</details>

### 思路

行查询只关心行号，列查询只关心列号。因此分别保存全部行号和全部列号，各自排序，重复坐标仍保留：同一行的两枚棋子应当贡献二。

![闭区间的数量由右侧尾后位置减去左侧起始位置](assets/bounds.svg)

对于排好序的坐标数组 $v$，$\verb@lower_bound(l)@$ 找到第一个大于等于 $l$ 的位置，$\verb@upper_bound(r)@$ 找到第一个大于 $r$ 的位置。两者之间恰好是区间内的所有棋子，数量为迭代器之差。

时间 $O(N\log N+Q\log N)$，空间 $O(N)$。网格坐标很大，不按 $H,W$ 开数组。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int H, W, N, Q;
    cin >> H >> W >> N >> Q;
    vector<int> rows(N), columns(N);
    for (int i = 0; i < N; ++i) cin >> rows[i] >> columns[i];
    sort(rows.begin(), rows.end());
    sort(columns.begin(), columns.end());
    while (Q--) {
        int type, l, r;
        cin >> type >> l >> r;
        const vector<int> &v = type == 1 ? rows : columns;
        // 第一个 > r 的位置，减去第一个 >= l 的位置。
        cout << upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l) << '\n';
    }
}
```

### 易错点

不能对重复行号或列号去重。右边界用 $\verb@upper_bound(r)@$，不是 $\verb@lower_bound(r)@$；所有查询区间均为闭区间。
