# P1918 数量到位置的有序映射 题解

## 目录

| 题号 | 题名 | 考点 | 难度 |
|---|---|---|---|
| A | 保龄球 | 模拟 | 1200 |

## A. 保龄球

> 原题：[P1918](https://www.luogu.com.cn/problem/P1918)
> 解法：数量到位置的有序映射 · C++17

### 题意

每个位置有不同瓶子数；每次询问某个瓶子数所在的位置，不存在时输出零。

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

### 从零讲：map 与 unordered_map：按键保存信息

需要按数值、字符串或状态查“次数、最优值、编号”时，可以用键值表。`map<Key,Value>` 保持键有序，查找、插入和删除为 $O(\log n)$；`unordered_map<Key,Value>` 用哈希分桶，常见情况下平均 $O(1)$，最坏可能 $O(n)$，也不保持键顺序。

```cxx
map<int,int> count;
for (int x : vector<int>{4, 2, 4}) ++count[x];
auto it = count.find(4);
if (it != count.end()) cout << it->second; // 2
```

`count[x]` 在键不存在时会插入一项，整数值初始化为零，适合计数。只想查询是否存在应使用 `find` 或 C++17 的 `count`，避免查询改变表。`find` 返回迭代器，读取前检查不是 `end()`。

`map` 的成员 `lower_bound(x)` 查首个不小于 `x` 的键，为 $O(\log n)$；无序表没有这种大小边界。键是一对或复杂结构时，需要与比较规则一致的排序规则，或合适的哈希与相等规则。

空间随不同键数量增长，为 $O(n)$。遍历 `map` 按键递增，遍历无序表没有稳定的大小顺序。哈希表扩容可能使迭代器失效；删除当前项后也不能继续读取它。若键范围很小且连续，用数组计数通常更直接，避免树或哈希的额外开销。

### 从零讲：迭代器、begin/end 与左闭右开范围

迭代器表示容器中的一个位置。`*it` 读取它指向的元素，`++it` 向后移动，`it == c.end()` 判断是否已经到尾后。把末尾之后的位置作为边界，使空范围、整个容器和一段子区间都能用同一形式表示。

```cxx
vector<int> a{4, 7, 9};
for (auto it = a.begin(); it != a.end(); ++it) {
    cout << *it << ' ';   // 输出 4 7 9
}
```

`[first,last)` 包含 `first`，排除 `last`。`[begin,begin)` 是空范围，`[begin,end)` 包含所有元素。不能读取 `*end()`；找不到时返回 `end()` 是合法结果，必须先判断再读取。

数组和 `vector` 的迭代器支持随机访问：`begin()+k` 跳到下标 $k$，`it-begin()` 得到下标，均为 $O(1)$。例如指向下标二的位置之前有零、一两个元素，故减起点也能表示前面有几个数。相减只对同一容器中可相减的迭代器有效。

`list`、`set`、`map` 的迭代器通常只能逐步移动，不支持 `it-begin()`。`distance(begin,it)` 可以计算距离，但在这些容器上需要走过中间位置，时间为 $O(k)$；不能因为写了一个函数就认为它是常数时间。

容器修改后，旧位置可能失效：`vector` 扩容会使旧位置失效，删除元素会影响该处及其后位置。需要跨修改保存“第几个”时可保存下标，再按新数据重新取得迭代器，同时核对下标是否仍然合法。

<!-- reusable-foundations:end -->

### 思路

读入时建立“瓶子数 → 原位置”的 map，每次 find 查询。

时间 $O((n+q)\log n)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;map<int,int> position;for(int i=1;i<=n;++i){int x;cin>>x;position[x]=i;}
int q;cin>>q;while(q--){int x;cin>>x;auto it=position.find(x);cout<<(it==position.end()?0:it->second)<<'\n';}
    return 0;
}
```

### 易错点

值与位置的角色不要颠倒；保留输入时的一基位置。

## 实测记录

本地 C++17 编译、1 组原站样例与 220 组独立边界/小域校验通过。
正文参考程序与源码逐字核对；没有向原站提交。
