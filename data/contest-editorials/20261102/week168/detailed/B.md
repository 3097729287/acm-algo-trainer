## B. 小月的屏幕

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/142559/B)

给定 $n\times m$ 的屏幕，$\verb@#@$ 表示故障像素，$\verb@.@$ 表示正常像素。统计最外圈中的 $\verb@#@$ 个数。$1\le n,m\le2000$，$nm\le4\times10^5$。

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

先看图中的四个绿色边缘。最上方的一行、最下方的一行、最左列和最右列共同组成外圈。

![绿色边界中的四个故障格被各计一次，中间两个不计](assets/border.svg)

如果把四条边分别求和，角会被两条边重复访问。更直接的办法是逐格扫描：读到一个格子时，判断它是否属于上述四条边的并集，只决定一次“计或不计”。

程序下标从零开始，所以边界条件是 $i=0$、$i=n-1$、$j=0$、$j=m-1$ 中至少一个成立，再检查当前字符是否为 $\verb@#@$。逻辑或 $\verb@||@$ 只给出一个真假结果，即使四个条件同时成立，也只执行一次累加。

例如 $n=1$ 时，每个格子都满足 $i=0$，整行都是外圈；无须另外补一份特殊处理。总共检查 $nm$ 个格子，时间 $O(nm)$；代码只保存当前行字符串，额外空间 $O(m)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, ans = 0;
    cin >> n >> m;
    for (int i = 0; i < n; ++i) {
        string s;
        cin >> s;
        for (int j = 0; j < m; ++j) {
            // 用一个条件取边界的并集，角和单行、单列均只计一次。
            if (s[j] == '#' && (i == 0 || i == n - 1 || j == 0 || j == m - 1)) ++ans;
        }
    }
    cout << ans << '\n';
}
```

### 易错点

四个角只计一次。$n=1$ 或 $m=1$ 时，所有格子都属于外圈；不要套用只适用于长宽至少为二的周长公式。
