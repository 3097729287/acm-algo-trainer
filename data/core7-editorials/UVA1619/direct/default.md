# UVA1619 固定正的区间最小值，向两边扩到更小值之前 题解

## 目录

| 题号 | 题名 | 考点 | 难度 |
|---|---|---|---|
| A | 感觉不错 Feel Good | 单调栈 + 前缀和 | 1500 |

## A. 感觉不错 Feel Good

> 原题：[UVA1619](https://www.luogu.com.cn/problem/UVA1619)
> 解法：固定正的区间最小值，向两边扩到更小值之前 · C++17

### 题意

求区间元素和乘最小值的最大值，平局依次取最短区间、最小左端点；多组数据之间空一行。

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

### 从零讲：单调结构的完整例子：首个更大位置与滑窗最大值

单调结构能够删候选，是因为已经证明被删者对未来不再有用，或它的答案此刻已经确定。单纯把数据排成单调顺序，并不能自动保证算法正确。

![四和一在六到来时找到首个更大位置，相邻二项窗口最大值为四和六](assets/foundations/monotone-structures.svg)

先看右侧第一个严格更大元素。栈保存尚未找到答案的下标，新下标$i$到来时，若它的值严格大于栈顶值，栈顶的答案就是$i$：之前已经扫描过的右侧元素都没能解决它，$i$自然是第一个。反复解决栈顶，再放入$i$。

严格大于时，只有旧值小于新值才弹出，相等不能回答询问。存下标而不只存数值，可以区分重复项、计算距离和输出位置。以下结果用一开始的下标，零表示没有答案。

再看长为$k$的窗口最大值。双端队列保存候选下标，队首最大。新值不小于一个队尾旧值，而且更晚过期，因此在旧值的全部剩余有效时间里都不劣于它，可以永久弹掉旧值。查询前还要从队首移走已经离开窗口的下标。

```cxx
#include <bits/stdc++.h>
using namespace std;
vector<int> nextGreater(const vector<long long>&a){
    vector<int>stack,answer(a.size());
    for(int i=0;i<int(a.size());++i){
        while(!stack.empty()&&a[stack.back()]<a[i]){
            answer[stack.back()]=i+1;
            stack.pop_back();
        }
        stack.push_back(i);
    }
    return answer;
}
vector<long long> slidingMaximum(const vector<long long>&a,int k){
    deque<int>queue;
    vector<long long>answer;
    for(int i=0;i<int(a.size());++i){
        while(!queue.empty()&&queue.front()<=i-k) queue.pop_front();
        while(!queue.empty()&&a[queue.back()]<=a[i]) queue.pop_back();
        queue.push_back(i);
        if(i>=k-1) answer.push_back(a[queue.front()]);
    }
    return answer;
}
int main(){
    vector<long long>a={4,1,6};
    auto next=nextGreater(a);
    auto maximum=slidingMaximum(a,2);
    for(int i=0;i<int(next.size());++i) cout<<(i?" ":"")<<next[i];
    cout<<'\n';
    for(int i=0;i<int(maximum.size());++i) cout<<(i?" ":"")<<maximum[i];
    cout<<'\n';
}
```

输出第一行三、三、零，表示四和一的首个更大位置都是第三项；不是输出更大的数值六。第二行四、六，对应窗口四一与一六的最大值。调用滑窗函数时要求一不大于$k$且$k$不大于数组长度。

vector用push_back、back、pop_back从末尾操作，适合栈；deque还能用front、pop_front从前端移走过期项。每次访问首尾之前都要先确认非空。循环中的while可能一次删很多项，但每个下标总共只加入、弹出一次，整体时间仍是线性的。

两段代码的等号处理不同有具体原因：第一个要求严格更大，相等不能解决；第二个只求最大值，同值新项更晚到期，旧项可删除。题目如果改成严格后缀纪录、重复次数统计或不同区间范围，需要重新判断等号和过期条件，不能机械套同一符号。

首个更大位置函数需要线性栈与结果数组；滑窗队列最多保存$k$个有效候选，结果向量仍可能是线性长度。若只需逐项输出滑窗结果，可以不保存结果向量。

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



![原样例最优端点三、五；边界值一与二严格小于四，将该最大可扩展跨度限制在中间三项。](assets/core7/UVA1619.svg)

每项用单调栈找左右最近严格更小值，之间是以它为最小值的最大可扩展区间。原数非负；最小值为正时向外加不小于它的数会严格增加区间和，因此只需评价这个完整跨度，区间和由前缀表取得。初始化答案为零和第一项，涵盖全零时的最短平局。按得分、长度、左端点比较。

每组时间 $O(n)$，空间 $O(n)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;bool first=true;
while(cin>>n){vector<long long>a(n),prefix(n+1);for(int i=0;i<n;++i){cin>>a[i];prefix[i+1]=prefix[i]+a[i];}
    vector<int>left(n),right(n),stack;
    for(int i=0;i<n;++i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();left[i]=stack.empty()?0:stack.back()+1;stack.push_back(i);}
    stack.clear();for(int i=n-1;i>=0;--i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();right[i]=stack.empty()?n-1:stack.back()-1;stack.push_back(i);}
    long long best=0;int bestLeft=0,bestRight=0;
    for(int i=0;i<n;++i){int l=left[i],r=right[i];long long value=a[i]*(prefix[r+1]-prefix[l]);if(value>best||(value==best&&make_pair(r-l,l)<make_pair(bestRight-bestLeft,bestLeft))){best=value;bestLeft=l;bestRight=r;}}
    if(!first) cout<<'\n';first=false;cout<<best<<'\n'<<bestLeft+1<<' '<<bestRight+1<<'\n';
}
    return 0;
}
```

### 易错点

原数组非负；边界取严格更小；正最小值扩展严格有利；全零选第一项；平局最短再最左；乘积六十四位；组间恰一空行，末尾换行。

## 实测记录

本地 C++17 编译、1 组原站样例与 183 组独立边界/小域校验通过。
正文参考程序与源码逐字核对；没有向原站提交。
