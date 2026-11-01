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

先任选一条准备补满的线。假设它有三个 $\verb@o@$ 和两个 $\verb@.@$，则这两个未标记格都必须补，至少两次；只补它们也确实足够，所以该线的代价就是空格数。

![图中主对角线四个格已经标记，中央空格是唯一需要补的格子](assets/bingo.svg)

获胜线总共十二条。先按行枚举，同时统计相应列；再单独统计两个对角线。程序下标从零开始，主对角线满足 $j=i$，副对角线满足 $j=4-i$。每统计完一条线，就用其中 $\verb@.@$ 的数量更新最小值。

为什么不会漏掉更好的方案？任何完成 Bingo 的结果至少有一条获胜线；它原先的所有 $\verb@.@$ 都已被补齐，操作数不可能比这条线的空格数还少。反过来，取十二条线中空格最少的那条，恰好补这些格子就能获胜。上下界相同。

已有 Bingo 时，一条线的空格数为零，答案自然为零。题目棋盘固定为五乘五，循环工作量是常数，时间、空间均为 $O(1)$。

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
