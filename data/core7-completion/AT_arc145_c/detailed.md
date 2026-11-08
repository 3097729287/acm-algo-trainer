## AT_arc145_c Split and Maximize

原题：[AT_arc145_c](https://www.luogu.com.cn/problem/AT_arc145_c)

### 从问题到算法

对 a<b<c<d，ab+cd 比 ac+bd 和 ad+bc 都大，交换论证说明最大乘积和唯一使用相邻数配对。因此问题变为：这些固定配对能否按相同次序出现在两个子序列中。

若两个配对的端点次序为 XYYX，外层 X 在一个子序列中早于 Y，在另一个中却晚于 Y，不能实现。反之，没有这种嵌套时，把每对先出现者放 A、后出现者放 B；各对的开始次序与结束次序相同，便能逐项配对。

将每对的先出现记左括号，后出现记右括号，得到合法括号序列。给定这个序列，不嵌套匹配必须按先进先出连接，恰好一种；合法括号序列共有 Catalan(N) 种。再为 N 对分配标签 N! 种、每对决定两个数的先后 2^N 种。答案为 Catalan(N)·N!·2^N=(2N)!·2^N/(N+1)!，在质数模下用逆元计算。

### 复杂度

时间 O(N+log MOD)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long P = 998244353;
    auto powmod = [&](long long a, long long b) {
        long long r = 1;
        for (; b; b >>= 1, a = a * a % P)
            if (b & 1)
                r = r * a % P;
        return r;
    };
    long long factorial = 1, denominator = 1;
    for (int i = 1; i <= 2 * n; i++) {
        factorial = factorial * i % P;
        if (i <= n + 1)
            denominator = denominator * i % P;
    }
    cout << factorial * powmod(denominator, P - 2) % P * powmod(2, n) % P << '\n';

    return 0;
}
```

### 实现提醒

禁止的是端点嵌套，允许交错；两侧子序列都要保持顺序；N! 不能遗漏。
