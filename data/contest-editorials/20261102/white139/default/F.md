## F. 小芳的最小生成树

### 题意

[原题链接](https://ac.nowcoder.com/acm/contest/141882/F)

给定正边权树 $T$，恰好添加 $n-1$ 条边，使所得图无自环、无重边。要求原树是唯一的最小生成树；删除任意一条原树边后，图仍连通，且最小生成树总权恰好比原树增加一。输出构造或 <code>No</code>。

每组 $4\le n\le2\times10^5$，原边权不超过 $10^9$，新增边权不超过 $2\times10^9$；所有测试的 $n$ 之和不超过 $2\times10^5$。

### 从零讲：边的结构体、pair、set 与引用

<details>
<summary>展开基础知识</summary>

<code>struct</code> 可以把一个对象的多个字段放在一起。例如 $\verb@struct Edge { int u,v,w; };@$ 保存边的两个端点和权值；$\verb@Edge e{1,3,6};@$ 建立一条边，$\verb@e.w@$ 访问权值。

$\verb@std::pair<int,int>@$ 保存两个整数，分别通过 <code>.first</code>、<code>.second</code> 访问。为了将无向边统一表示，先把端点排成较小值在前，例如把 $(3,1)$ 统一成 $(1,3)$。两个 <code>pair</code> 的默认比较先比第一项，第一项相等再比第二项。

$\verb@std::set<T>@$ 维护不重复的、有序的元素集合，需要 set；<code>pair</code> 需要 utility。底层平衡搜索树使插入、查找的时间为 $O(\log m)$，保存 $m$ 项使用 $O(m)$ 空间。

```cxx
set<pair<int,int>> edges;
auto result = edges.insert({1, 3}); // 第一次插入
bool fresh = result.second;        // true
bool again = edges.insert({1, 3}).second; // false，没有再加一项
```

<code>insert</code> 返回一个二元组：第一项是指向集合中该值的迭代器，第二项是本次是否新插入。这里只需第二项即可完成去重，无须解引用迭代器。<code>set</code> 中元素不能直接修改；要改变键应先删除旧键再插入新键。

$\verb@const Edge &e = edges[i]@$ 给原数组元素取只读别名，避免复制。要保证引用使用期间元素仍存在且数组未扩容。本题 <code>edges</code> 一开始就固定大小，此后不追加，所以该引用有效。$\verb@for (int v : {e.u,e.v})@$ 依次取两个端点；$\verb@for (const Edge &e : added)@$ 依次只读访问已构造的边。这两种范围循环都按元素数量计算时间。

</details>

### 从零讲：vector 的大小与引用有效期

<details>
<summary>展开基础知识</summary>

$\verb@std::vector<T>@$ 是连续存放同一种类型元素的动态数组，需要 vector。$\verb@std::vector<int> a(n,0);@$ 建立恰好 $n$ 个零，合法下标为 $0$ 到 $n-1$；$\verb@vector<int> pos(n+1)@$ 则可使用下标 $n$。建数组需要 $O(n)$ 时间与空间，按下标访问为 $O(1)$。

```cxx
vector<int> a(3, 0);
a[1] = 7;                  // 现在是 0,7,0
a.push_back(9);             // 尾部追加，现在有四项
int last = a.back();        // 返回最后一项 9，不删除
a.pop_back();              // 删除最后一项，不返回它
```

$\verb@size()@$ 返回当前元素数量；$\verb@push_back@$ 均摊为 $O(1)$，扩容时会搬运已有元素，所以单次可能为 $O(n)$。$\verb@pop_back@$ 为 $O(1)$，空数组不能调用 <code>back</code> 或 $\verb@pop_back@$，也不能访问 $\verb@a[0]@$。$\verb@operator[]@$ 不负责检查越界。

扩容会使原来的迭代器、指针和引用失效；需要长期引用某一元素时，要确认之后不会扩容。$\verb@size()@$ 的返回类型是无符号整数，避免空数组上写 $\verb@size()-1@$。$\verb@static_cast<int>(a.size())@$ 是显式转成整数，应先保证数量没有超过 $\verb@int@$ 的表示范围。

</details>

### 思路

做法是：**对每条原树边，找一条与它共享端点、权值不更大的另一条树边，把这条二边路径的两端相连，新权值取当前边权加一。** 找不到这样的邻边时无解；最后去重，并用很重的非树边补足数量。

#### 为什么这样的替代边有效

树中两点间有唯一一条路径。给它们加边就会形成一个环。要保持原树是唯一最小生成树，新增边必须严格重于这条原路径上的每条边；否则用它换掉路径最大边，会得到更优或同样优的生成树。

反过来，这个条件也充分：在任何另一棵生成树中，取一条新增边，删除它形成两部分；原树中连接其两端的路径必有一条边跨越这两部分。换入这条原树边，权值严格减小。反复替换最终回到原树，所以其他生成树都更重。

![二边路径上的局部替代](assets/f-local.svg)

设当前边权为 $w$，旁边另一条边的权值不超过 $w$。连接二边路径两端并赋权 $w+1$，既严格重于路径最大边，又能在当前树边被删后接通两部分，总权从 $x$ 变为 $x+1$。由于原树唯一最优、边权均为整数，删边后的任何生成树权值都至少是 $x+1$，所以这棵恰好最优。

#### 为什么找不到较轻邻边就无解

上面的交换过程每换掉一条新增边，总权至少减少一。如果某棵树总权只有 $x+1$，它最多含一条新增边，因此必须形如“原树删掉当前边，再加一条替代边”。替代边的权值必须为 $w+1$。

![孤立最轻边造成的矛盾](assets/f-obstruction.svg)

这条替代边不能与原树边重合，所以原路径至少含两条边，且经过当前被删边。路径上必有另一条与当前边相邻的树边。若所有邻边都严格重于 $w$，新增边要比路径最大边更重，整数权值就至少为 $w+2$，与 $w+1$ 矛盾。

因此，“每条边都有另一条权值不更大的邻边”是充要条件。

#### 怎样实现并恰好添加指定数量

每个顶点记录权值最小和次小的两条边的**编号**。处理边 $e$ 时，分别在两端找除自己之外的最轻边；若最轻边就是自己，就查次轻边。任一端找到权值不超过 $w_e$ 的候选即可。

连接二边路径两端不会产生原树边，否则原树中已经有三角环。用 <code>set</code> 统一保存按端点大小排序后的无向边对，过滤重复新增边。如果同一二边路径的两条边都提出同一方案，两边权值必然相等，新增权值也相同，保留一次仍能服务两条树边。

![完整四点构造与补足边](assets/f-complete.svg)

每条原树边最多提出一条方案，去重后至多 $n-1$ 条。不足时依次枚举还没出现的点对，赋权 $2\times10^9$。它严格重于所有原树边，仍满足唯一最小生成树条件；已有替代方案也仍在。

可用非树边共有 $\binom n2-(n-1)=(n-1)(n-2)/2$ 条。因为 $n\ge4$，至少有 $n-1$ 条，能够补足。虽然代码用了两层枚举，但只扫到足额就停止：被跳过的已有边对不足 $2n$，成功加入的不足 $n$，总共只检查 $O(n)$ 个点对。

时间复杂度 $O(n\log n)$，额外空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Edge {
    int u, v, w;
};

pair<int, int> key(int u, int v) {
    if (u > v) swap(u, v);
    return {u, v};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<Edge> edges(n - 1);
        vector<int> first(n + 1, -1), second(n + 1, -1);
        set<pair<int, int>> used;
        for (int i = 0; i < n - 1; ++i) {
            Edge &e = edges[i];
            cin >> e.u >> e.v >> e.w;
            used.insert(key(e.u, e.v));
            for (int v : {e.u, e.v}) {
                // 每个顶点保存最轻和次轻的两条边的编号。
                if (first[v] == -1 || e.w < edges[first[v]].w) {
                    second[v] = first[v];
                    first[v] = i;
                } else if (second[v] == -1 || e.w < edges[second[v]].w) {
                    second[v] = i;
                }
            }
        }
        vector<Edge> added;
        bool ok = true;
        for (int i = 0; i < n - 1; ++i) {
            const Edge &e = edges[i];
            int center = e.u, end = e.v;
            int j = (first[center] == i ? second[center] : first[center]);
            if (j == -1 || edges[j].w > e.w) {
                center = e.v;
                end = e.u;
                j = (first[center] == i ? second[center] : first[center]);
            }
            if (j == -1 || edges[j].w > e.w) {
                ok = false;
                break;
            }
            int other = edges[j].u + edges[j].v - center;
            pair<int, int> p = key(end, other);
            // 距离为二的两个端点一定不是原树边；重复方案只留一次。
            if (used.insert(p).second) added.push_back({p.first, p.second, e.w + 1});
        }
        if (!ok) {
            cout << "No\n";
            continue;
        }
        // 补足 n-1 条。已有边对不足 2n，扫描到足额只需 O(n) 次候选。
        for (int u = 1; u <= n && static_cast<int>(added.size()) < n - 1; ++u) {
            for (int v = u + 1; v <= n && static_cast<int>(added.size()) < n - 1; ++v) {
                if (used.insert({u, v}).second) added.push_back({u, v, 2000000000});
            }
        }
        cout << "Yes\n";
        for (const Edge &e : added) cout << e.u << ' ' << e.v << ' ' << e.w << '\n';
    }
}
```

### 易错点

“另一条边”必须排除当前边自身，等权邻边合法。无向点对先规范顺序再去重；替代边去重后仍需补到恰好 $n-1$ 条。不能只检查全局最小权值是否重复。
