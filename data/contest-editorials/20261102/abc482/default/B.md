## B. Blank Bingo

### 题意

[原题链接](https://atcoder.jp/contests/abc482/tasks/abc482_b)

给定 $5\times5$ 棋盘，$\verb@o@$ 已标记，$\verb@.@$ 未标记。最少补多少个标记，才能让某一整行、整列或完整对角线的五格全部标记？

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

一共只有十二条可能获胜的线：五行、五列和两条对角线。固定一条线时，补齐它的最少操作数恰好是其中的 $\verb@.@$ 数量。枚举十二条线并取最小值即可。

![主对角线只缺中央一格](assets/bingo.svg)

枚举涵盖任意获胜方案中的那条完整线，也能按计得的代价补齐它，所以最小值就是答案。棋盘大小固定，时间、空间均为 $O(1)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    vector<string> s(5);
    for (auto &row : s) cin >> row;
    int answer = 5;
    for (int i = 0; i < 5; ++i) {
        int row = 0, column = 0;
        for (int j = 0; j < 5; ++j) { row += s[i][j] == '.'; column += s[j][i] == '.'; }
        answer = min(answer, min(row, column));
    }
    int main_diagonal = 0, other_diagonal = 0;
    for (int i = 0; i < 5; ++i) { main_diagonal += s[i][i] == '.'; other_diagonal += s[i][4 - i] == '.'; }
    cout << min(answer, min(main_diagonal, other_diagonal)) << '\n';
}
```

### 易错点

需要五个格全部在棋盘内的完整对角线，只有两条。把未标记格 $\verb@.@$ 作为代价；已经 Bingo 时答案为零。
