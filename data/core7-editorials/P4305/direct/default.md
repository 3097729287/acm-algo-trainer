# P4305 集合判重并保留读入顺序 题解

## 目录

| 题号 | 题名 | 考点 | 难度 |
|---|---|---|---|
| A | 不重复数字 | 模拟 | 1200 |

## A. 不重复数字

> 原题：[P4305](https://www.luogu.com.cn/problem/P4305)
> 解法：集合判重并保留读入顺序 · C++17

### 题意

去掉重复数字，只输出每个值第一次出现时的那一份，保持首次出现顺序。

<!-- reusable-foundations:start -->

### 从零讲：C++ 输入输出：把数据读进变量，把结果写到标准输出

程序运行时从标准输入接收题目给的数据，把答案送到标准输出。`cin` 和 `cout` 定义在 `<iostream>`；写 `using namespace std;` 后可以省略它们前面的 `std::`。最小完整程序是：

```cxx
#include <iostream>
using namespace std;
int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << '\n';
    return 0;
}
```

输入二十和三十，两个变量分别保存二十、三十，输出五十。`int a, b;` 声明两个整数变量；`cin >> a` 才给变量赋入输入值。多个 `>>` 从左到右读取，读取整数时会跳过空格、制表符、换行，所以两个整数可以分处两行。负号属于整数，不需要另读一个符号。

`cout <<` 后可以接数值、字符或字符串。`' '` 是一个空格字符，`'\n'` 是换行字符，`"Hello"` 是字符串。`cout << a << ' ' << b << '\n';` 输出两个以空格分开的整数并换行。评测程序只需要答案，不应加入“请输入”等提示。

读取 `char c; cin >> c;` 会跳过前导空白。要读取包含空格的一整行，用 `<string>` 中的 `string s; getline(cin, s);`。若此前用 `cin >> n` 读取过整数，换行还留在输入中，需要先处理那一个剩余换行；不能盲目把所有空格都删掉，因为字符画的行首空格和文本中的空格可能就是数据。

`fixed << setprecision(3)`（需要 `<iomanip>`）表示以小数形式保留三位小数，例如把 $2.5$ 输出成 $2.500$；不用 `fixed` 时，`setprecision` 指有效数字总数。设置会影响后续输出，使用前应确认所需精度。

竞赛中可在首次输入输出前调用 `ios::sync_with_stdio(false); cin.tie(nullptr);`，减少 C++ 流与 C 标准输入输出的同步、绑定开销。随后保持使用 `cin/cout`，不要混用另一套 `scanf/printf`。交互题还要在需要对方回应前主动刷新，例如 `cout << query << endl;`；普通题用换行字符即可。

读入长度为 $L$ 的文本、或输出 $L$ 个字符，至少需要 $O(L)$ 时间。数据类型仍要能容纳结果：把两个整数相乘时，即使保存到 `long long`，也要让乘法本身在这个类型中进行，例如先把输入声明为 `long long`。

### 从零讲：set、multiset 与有序邻居

`set<T>` 保留互不相同的元素并按比较器排序，适合动态判断存在、查前驱后继；`multiset<T>` 允许重复值。插入、按键查找和成员二分通常为 $O(\log n)$，空间为 $O(n)$。`unordered_set` 是哈希集合，平均查询快，但没有大小顺序。

```cxx
set<int> s{2, 5, 9};
auto it = s.lower_bound(6); // 指向 9，第一个 >=6 的数
if (it != s.end()) cout << *it;
if (it != s.begin()) cout << *prev(it); // 前驱是 5
```

`lower_bound` 等于 `end()` 表示没有更大的候选；它仍可能有前驱。等于 `begin()` 表示没有前驱，不能再向前移动。空集合尤其要先检查。

`multiset` 中 `erase(value)` 删除所有等于该值的项；只删一个应先 `find`，确认找到后 `erase(it)`。`set` 会自动去重，若多个相同记录必须各算一次，就不能直接把它们塞进普通集合后拿集合长度作答案。

关联容器的迭代器不支持相减。查询边界位置快，不等于“边界前有几个元素”也能快；对 `set` 调 `distance(begin,it)` 可能走过线性多个节点。大量秩查询可考虑离散化加树状数组或支持秩的数据结构。

### 从零讲：pair、tuple 与结构化绑定

有些数据天然需要成组：一个区间有两个端点，一个队列状态有坐标和距离。`pair<A,B>` 保存两项，用 `.first`、`.second` 读取；`tuple<A,B,C>` 可保存更多项，用 `get<0>(t)` 等读取。分别需要 `<utility>`、`<tuple>`。

C++17 的结构化绑定能为一组分量起局部名字：

```cxx
pair<int,int> point{3, 5};
auto [x, y] = point;      // 复制出两个分量
x = 9;                  // point.first 仍为 3
auto& [u, v] = point;    // 绑定原对象的分量
u = 7;                  // point.first 变为 7
```

`for (auto [l,r] : segments)` 每轮读取一对值；`for (const auto& [l,r] : segments)` 以只读引用读取，避免复制；需要修改原记录时才用 `auto&`。引用必须在原对象还存在且位置未失效时使用。

`pair` 和 `tuple` 的默认比较是字典序：从第一项起，第一个不同的分量决定顺序。`priority_queue<pair<int,int>>` 因而先比较第一项，再以第二项破同分，不能误认为只看第一项。这类语法只让记录组织和访问更清楚，拆分本身的成本取决于分量是否需要复制。

<!-- reusable-foundations:end -->

### 思路

从左到右读，set 尚未包含当前值时立即输出并插入；已经包含则跳过。每组数据重建集合。

每组时间 $O(n\log n)$、空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){int n;cin>>n;set<int> seen;bool first=true;
    while(n--){int x;cin>>x;if(seen.insert(x).second){if(!first)cout<<' ';cout<<x;first=false;}}
    cout<<'\n';
}
    return 0;
}
```

### 易错点

不能通过遍历有序集合输出答案；每组清空历史，支持负数。

## 实测记录

本地 C++17 编译、1 组原站样例与 220 组独立边界/小域校验通过。
正文参考程序与源码逐字核对；没有向原站提交。
