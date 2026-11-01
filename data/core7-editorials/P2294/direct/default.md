# P2294 区间收入改成前缀和之差，用带权并查集判矛盾 题解

## 目录

| 题号 | 题名 | 考点 | 难度 |
|---|---|---|---|
| A | 狡猾的商人 | 并查集 + 前缀和 | 1800 |

## A. 狡猾的商人

> 原题：[P2294](https://www.luogu.com.cn/problem/P2294)
> 解法：区间收入改成前缀和之差，用带权并查集判矛盾 · C++17

### 题意

若干条记录给出连续月份的收入总和，收入允许为负。判断是否存在一份月收入账本同时满足所有记录，每组输出小写 true 或 false。

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

### 从零讲：分支与循环：按条件选择，按次序重复

`if (条件) { ... } else { ... }` 根据条件的真假选择一条分支。比较运算 `==`、`!=`、`<`、`<=`、`>`、`>=` 返回真假值；`=` 是赋值，不能代替相等比较。`&&` 表示两边都成立，`||` 表示至少一边成立，`!` 把真假反转。

```cxx
int score = 85;
if (score >= 90) cout << "A";
else if (score >= 60) cout << "B";
else cout << "C"; // 这个例子输出 B
```

这条分支链只执行第一个符合条件的分支。先处理高分后，第二个条件自然只会接到低于九十分的数。几个独立的 `if` 则可能执行多次；两种结构代表不同问题。逻辑运算会短路：`i < n && a[i] == 0` 先确认下标合法，才读取那一格。

`for (初始化; 继续条件; 每轮更新)` 适合知道重复范围的情况。例如下列代码依次处理一到四，总和是十：

```cxx
int sum = 0;
for (int i = 1; i <= 4; ++i) {
    sum += i;
}
cout << sum;
```

初始化只做一次；每轮先判断条件，条件为真才执行循环体，随后执行更新。`++i` 把 $i$ 加一，`sum += i` 等价于把旧 sum 加 $i$ 再保存。应明确每个变量在循环前、循环后分别表示什么；最大值相同时是否更新，决定了保留较早还是较晚的答案。

`while (条件)` 适合“不满足目标就再做一步”：

```cxx
int x = 13, times = 0;
while (x > 1) {
    x /= 2;
    ++times;
}
// x 依次是 13、6、3、1，执行三次
```

循环开始前先检查条件，初始已满足目标时可能一次也不执行。每次执行必须推进状态，否则可能无限循环。`break` 结束最内层循环，`continue` 跳过本轮剩余部分；`for` 中的 continue 之后仍会执行每轮更新。

复杂度由实际执行次数决定。上述求和执行 $n$ 次是 $O(n)$；每次将正整数减半只执行 $O(\log n)$ 次。两层循环不能仅凭外观判定为平方：内层若总共只前进 $n$ 次，总量仍可能线性。变量应在正确作用范围初始化；多组数据的计数器若未重置，下一组会错误继承上一组结果。

### 从零讲：vector：长度可变的连续数组

`vector<T>` 保存一串同类型的元素，适合按下标访问、扫描、排序。`T` 是元素类型，例如 `vector<int>` 保存整数，`vector<pair<int,int>>` 保存整数对，`vector<vector<int>>` 可保存每个顶点各自的邻居。需要 `<vector>`。

```cxx
vector<int> a(3, 7);   // 三个元素，内容是 7、7、7
a.push_back(9);       // 在末尾追加，现在长度为 4
int x = a[1];         // 从 0 编号，这里得到 7
a[1] = 2;            // 改第二个元素
int n = int(a.size());
```

`vector<int> a(3)` 创建三个值为零的元素；`a.reserve(3)` 只预留容量，元素数仍为零，此时不能访问 `a[0]`。长度 `size()` 与容量 `capacity()` 是不同概念。

下标访问为 $O(1)$，遍历为 $O(n)$。末尾追加通常为 $O(1)$；容量不足时会分配更大的连续空间并搬移元素，这次可能为 $O(n)$，一连串追加的平均成本称为摊还 $O(1)$。中间插入或删除会搬移后续元素，最坏 $O(n)$。内存是元素量的 $O(n)$，并可能预留部分尚未使用的容量。

`begin()` 指向首元素，`end()` 指向尾后位置，`sort(a.begin(),a.end())` 操作整个数组。`a[i]` 不检查越界；下标须满足 $0\le i<\mathrm{size}$。`at(i)` 会检查越界并抛异常。空数组不能访问 `front()`、`back()`；`pop_back()` 也要求非空。

扩容后指向旧存储的迭代器、引用和指针会失效。遍历的同时 `push_back`，不能假定此前取得的引用仍可用。读取大数组的函数常用 `const vector<int>& a` 按常量引用传入，既不复制也禁止通过该引用修改；`vector<int> a` 按值传参则复制内容。选择副本还是引用取决于是否要保留独立数据。

### 从零讲：整数类型、整除与溢出

计算前先看每一步可能达到的范围。常见环境中 `int` 是 32 位，上界约 $2.1\times10^9$；`long long` 至少 64 位，常见有符号 64 位上界约 $9.22\times10^{18}$。`using ll = long long;` 只是为已有类型起别名。

```cxx
int a = 100000, b = 100000;
long long wrong = a * b;      // 右边先按 int 乘，可能已溢出
long long right = 1LL * a * b; // 先把运算提升到 long long
```

不能指望“接收结果的变量够大”修复此前已经溢出的计算。先提高操作数类型，再做乘法。超过 64 位时，GCC 的 `__int128` 可作中间量，但它不是标准 C++17 类型，也没有标准流输出重载；先证明范围，再选择工具。

整数 `/` 对有符号数向零截断：`7/3==2`、`-7/3==-2`。对非负数才等于向下取整。余数满足 `a == (a/b)*b + a%b`，除数不能为零；要将余数归入 $[0,m-1]$（$m>0$），可用 `(a % m + m) % m`，同时保证中间加法不溢出。

非负 $a$、正 $b$ 的向上取整可写 `a/b + (a%b != 0)`，比 `(a+b-1)/b` 更容易避免加法溢出。比较平方时也应在宽类型内计算；浮点数不适合作为大整数相等的默认判断方式。

`size()` 返回无符号类型。空容器上写 `size()-1` 会绕到很大的数，逆序遍历可以先转成有符号、确认长度，或使用逆向迭代器。`abs` 对最小有符号数无法在同类型中表达其正值，需先约束输入差值范围。一般机器整数运算按常数时间估算，宽类型解决表示范围，不改变算法的增长阶。

### 从零讲：具名函数：给可复用计算一个明确接口

函数把一段计算包装成“输入参数 → 返回结果”。例如判断整数是否为偶数：

```cxx
bool even(int x) {
    return x % 2 == 0;
}
int main() {
    bool a = even(8); // a 为 true
    bool b = even(7); // b 为 false
}
```

`bool` 是返回类型，`even` 是函数名，`int x` 是参数声明。调用 `even(8)` 时，实参八传入这个新调用的局部变量 $x$，执行 return 后把真假值交回调用处。定义本身不执行计算，只有调用才执行。函数应在调用处之前定义，或提前写声明。

普通数值参数按值传递，函数里修改 $x$ 不会改变调用者原变量。参数写成 `int &x` 时才引用调用者对象；必须让这个对象在调用期间有效。`const vector<int>& a` 用引用避免复制整个容器，并承诺不通过这个引用修改它。返回局部变量的值是安全的，返回局部变量的引用则在函数结束后失效。

函数名应说明它回答的问题，调用处负责传哪些数据。例如闰年判定只接收一个年份并返回真假，枚举年份范围和输出格式由调用者处理。同一判定被多次使用时，这能减少规则不一致；但函数包装不会自动降低算法复杂度，仍要把每次调用实际做的工作计入时间。

如果函数内部又调用自身，就是递归，需要明确最小情况如何直接返回、每次调用如何逼近它；递归会占用调用栈。普通辅助函数可以不使用递归，不应仅因写成函数就称作递归算法。

### 从零讲：并查集：维护哪些对象已属于同一组

从每个元素独立成组开始，反复合并两组、判断两项是否连通。并查集用父指针形成若干棵树，每棵树的根代表一组；根的编号只是代表，不一定是最小编号或有特殊题意。

![合并两个根后，同组元素沿父指针到达同一代表；路径压缩缩短后续查找](assets/foundations/dsu.svg)

```cxx
struct DSU {
    vector<int> parent, size;
    DSU(int n): parent(n), size(n, 1) {
        iota(parent.begin(), parent.end(), 0);
    }
    int find(int x) {
        return parent[x] == x ? x : parent[x] = find(parent[x]);
    }
    bool merge(int a, int b) {
        a = find(a); b = find(b);
        if (a == b) return false;
        if (size[a] < size[b]) swap(a, b);
        parent[b] = a; size[a] += size[b];
        return true;
    }
};
```

合并 $0,1$ 再合并 $1,2$ 后，三者的 `find` 相同，即使零和二没有直接边。这表示路径连通，不表示两项相邻。路径压缩将访问链上的父亲直接改为根；按大小合并把小树挂到大树，避免人为形成长链。

初始化 $O(n)$，两种优化一起使用时，一连串操作的摊还成本为 $O(\alpha(n))$ 每次，常见规模近似常数；不能说每一次都严格 $O(1)$。数组空间 $O(n)$。

普通并查集擅长增加连通关系，不直接支持删边和拆组。回滚版本通常不用路径压缩，并保存每次合并改变的值；带权版本还需维护到父亲的关系，不能只合并普通 parent。分组大小等统计应读根上的记录。

### 从零讲：前缀和：一段和由两段前缀相减

一串数需要反复询问连续一段的总和，逐段扫描会重复加很多相同元素。先保存从头到每个位置的累计量，就能复用这些工作。

对从一编号的数组定义 $S_0=0$，$S_i=a_1+\cdots+a_i$。例如 $a=[2,3,1,4]$，前缀为 $S=[0,2,5,6,10]$。

![S4 包含整段，S1 是多算的前缀，减去后留下第 2 至 4 项](assets/foundations/prefix.svg)

查询 $[2,4]$ 时，$S_4$ 包含第一个数，减去 $S_1$ 后留下 $3+1+4=8$。一般地，$S_r-S_{l-1}$ 中前 $l-1$ 项逐项抵消，只留下第 $l$ 到第 $r$ 项。

```cxx
vector<long long> s(n + 1, 0);
for (int i = 1; i <= n; ++i) s[i] = s[i - 1] + a[i];
long long sum = s[r] - s[l - 1];
```

预处理 $O(n)$ 时间和空间，每次查询 $O(1)$，比 $q$ 次逐段扫描的最坏 $O(nq)$ 更适合大量静态区间和。若使用从零编号的原数组，也可定义 $P_i$ 为前 $i$ 项之和，查询闭区间 $[l,r]$ 为 $P_{r+1}-P_l$；不要混用两套下标。

前缀可以累积满足条件的次数，把每项变成零或一；也可以保存异或，此时相同前缀通过异或抵消。最小值没有同样的可逆减法，不能直接套区间最小值。原数组改变后，后续许多前缀都受影响；频繁在线修改时可考虑树状数组或线段树。

首个空前缀零不可漏，累加类型要覆盖总和。数学上的减法可能得到负值，别让无符号类型把它变成巨大正数。

### 从零讲：带权并查集：保存坐标差，不把代表编号当实际位置

普通并查集只回答两个对象是否同组。如果还给出“$y$ 的坐标减 $x$ 的坐标等于 $v$”，就要在父指针旁保存差值。坐标可以代表收入前缀、距离或时刻；它们不一定是非负数，也不一定必须知道绝对值。

#### 差值沿父链相加

定义 $offset[x]$ 为 $X[x]-X[parent[x]]$。根指向自己，偏移为零。若二号的父亲是一号，偏移负二，而一号到零号的偏移为四，则二号到零号的偏移是负二加四，等于二。

![压缩前沿父指针累计差值，压缩后偏移直接表示到根的差](assets/foundations/weighted-dsu.svg)

路径压缩不仅改父亲，也要改偏移。先保存旧父亲，递归使旧父亲到根的偏移算好，再累加到当前点；否则会出现“父亲已是根，偏移却还只到旧父亲”的不一致。

#### 两组之间的新差怎样推

压缩 $x$、$y$ 后，设两根为 A、B，已知 $dx=X[x]-X[A]$、$dy=X[y]-X[B]$。要加入 $X[y]-X[x]=v$，代入得到

$$X[B]-X[A]=v+dx-dy.$$

若 B 挂到 A，就把右侧存到 $offset[B]$；反向挂接则存相反数。按大小合并时可以任选根的身份，但不能只交换编号而沿用原差的符号。

同根时根坐标抵消，只需检查 $dy-dx$ 是否等于 $v$。不等说明原约束链与新约束组成矛盾环。不同根时两组原本可独立整体平移，设置根差即可满足约束，不会破坏任一组内部已有关系。

```cxx
#include <bits/stdc++.h>
using namespace std;
struct WeightedDSU {
    vector<int> parent, size;
    vector<long long> offset;
    WeightedDSU(int n):parent(n+1),size(n+1,1),offset(n+1) {
        iota(parent.begin(),parent.end(),0);
    }
    int find(int x) {
        if(parent[x]==x)return x;
        int old=parent[x];
        parent[x]=find(old);
        offset[x]+=offset[old];
        return parent[x];
    }
    bool constrain(int x,int y,long long v) {
        int a=find(x),b=find(y);
        long long difference=v+offset[x]-offset[y];
        if(a==b)return difference==0;
        if(size[a]>=size[b]) {
            parent[b]=a;offset[b]=difference;size[a]+=size[b];
        } else {
            parent[a]=b;offset[a]=-difference;size[b]+=size[a];
        }
        return true;
    }
};
int main() {
    WeightedDSU groups(3);
    groups.constrain(0,3,0);
    groups.constrain(1,2,-2);
    groups.constrain(0,1,4);
    groups.find(2);groups.find(0);
    long long delta=groups.offset[2]-groups.offset[0];
    bool valid=groups.constrain(0,2,2);
    bool conflict=groups.constrain(0,2,3);
    cout<<delta<<' '<<valid<<' '<<conflict<<'\n'; // 2 1 0
}
```

代码下标零到 $n$ 均可使用；负偏移合法。比较两个偏移前先对两个点分别 find，确保它们都已表示到根的差。只有同根才能相减得到确定关系，不同组的偏移各有自己的坐标原点。

普通标量差的合并和路径压缩均为常数次算术操作，按大小合并与路径压缩共同使用时，每次摊还 $O(\alpha(n))$，数组空间 $O(n)$。关系若是异或、模数或其它组合运算，必须重新定义合成与反向规则，不能机械沿用加减公式。

<!-- reusable-foundations:end -->

### 思路

设 $S[i]$ 为前 $i$ 月总收入，记录 $s$ 到 $t$ 收入 $v$ 等价于 $S[t]-S[s-1]=v$。在前缀下标零到 $n$ 上建带权并查集，$offset[x]$ 保存 $S[x]-S[parent[x]]$。两端同根时检查已有差值；不同根时按等式推导两根之差后合并，不能把区间当成相同组直接合并。

每组时间 $O(n+m\alpha(n))$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
struct WeightedDSU{
    vector<int>parent,size;vector<long long>offset;
    WeightedDSU(int n):parent(n+1),size(n+1,1),offset(n+1){iota(parent.begin(),parent.end(),0);}
    int find(int x){if(parent[x]==x)return x;int old=parent[x];parent[x]=find(old);offset[x]+=offset[old];return parent[x];}
    bool constrain(int x,int y,long long value){
        int a=find(x),b=find(y);long long difference=value+offset[x]-offset[y];
        if(a==b)return difference==0;
        if(size[a]>=size[b]){parent[b]=a;offset[b]=difference;size[a]+=size[b];}
        else{parent[a]=b;offset[a]=-difference;size[b]+=size[a];}
        return true;
    }
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;WeightedDSU groups(n);bool possible=true;
    for(int i=0;i<m;++i){int s,t;long long value;cin>>s>>t>>value;if(!groups.constrain(s-1,t,value))possible=false;}
    cout<<(possible?"true":"false")<<'\n';
}
    return 0;
}
```

### 易错点

前缀下标是 $s-1$ 与 $t$；压缩时累计偏移；反向挂根需反号；负收入合法；读完全部记录。

## 实测记录

本地 C++17 编译、1 组原站样例与 24 组独立边界/小域校验通过。
正文参考程序与源码逐字核对；没有向原站提交。
