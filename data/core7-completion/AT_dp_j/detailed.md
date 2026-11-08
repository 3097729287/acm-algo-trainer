## AT_dp_j Sushi

原题：[AT_dp_j](https://www.luogu.com.cn/problem/AT_dp_j)

### 从问题到算法

盘子编号不影响之后的随机选择，只需要知道三类非空盘的数量。设 E(a,b,c) 为从当前状态吃完所需的期望操作数。选中一寿司盘后变为 (a−1,b,c)，二寿司盘变为 (a+1,b−1,c)，三寿司盘变为 (a,b+1,c−1)。

每次无论选中什么都花费一步，另有 (n−a−b−c)/n 的概率选中空盘并保持原状态。因此 E=1+[aE1+bE2+cE3+(n−a−b−c)E]/n。把自身项移到左边，便得到实现中的除式。

空状态 E(0,0,0)=0。按 c、b、a 依次递增枚举，二寿司转移用到更小的 b，三寿司转移用到更小的 c，都已计算。只存 a+b+c<=n 的状态。使用 double 输出足够精度。

### 复杂度

时间 O(n³)，空间 O(n³)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    int count[4] = {};
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        count[x]++;
    }
    int side = n + 2;
    vector<double> dp((size_t)side * side * side);
    auto at = [&](int a, int b, int c) -> double & {
        return dp[((size_t)c * side + b) * side + a];
    };
    for (int c = 0; c <= n; c++)
        for (int b = 0; b + c <= n; b++)
            for (int a = 0; a + b + c <= n; a++) {
                if (a + b + c == 0)
                    continue;
                double value = n;
                if (a)
                    value += a * at(a - 1, b, c);
                if (b)
                    value += b * at(a + 1, b - 1, c);
                if (c)
                    value += c * at(a, b + 1, c - 1);
                at(a, b, c) = value / (a + b + c);
            }
    cout << fixed << setprecision(12) << at(count[1], count[2], count[3]) << '\n';

    return 0;
}
```

### 实现提醒

分子常数是总盘数 n；分母是非空盘数；不能忽略选到空盘的操作。
