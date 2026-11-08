## P6146 Help Yourself G

原题：[P6146](https://www.luogu.com.cn/problem/P6146)

### 从问题到算法

固定线段 i，若它的左端点是某个并集连通块的最左点，i 必须被选择，所有覆盖这个左端点的其它线段都不能选择；剩下线段任意选。

端点两两不同，因此覆盖其左端点的其它线段恰好是扫描时已开始且未结束的 c 条线段。自由选择的线段有 N−1−c 条，贡献为二的该次方。

每个子集的每个连通块都由唯一最左端点计一次，总贡献正好是所有复杂度之和。端点范围是一到二 N，可以直接建立起终事件数组，线性扫描。

### 复杂度

时间 O(N)，空间 O(N)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
long long power(long long a, long long b) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % MOD)
        if (b & 1)
            r = r * a % MOD;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> event(2 * n + 2);
    for (int i = 0; i < n; i++) {
        int l, r;
        cin >> l >> r;
        event[l] = 1;
        event[r] = -1;
    }
    vector<long long> two(n + 1, 1);
    for (int i = 1; i <= n; i++)
        two[i] = two[i - 1] * 2 % MOD;
    int active = 0;
    long long ans = 0;
    for (int x = 1; x <= 2 * n; x++) {
        if (event[x] == 1) {
            ans = (ans + two[n - 1 - active]) % MOD;
            active++;
        } else if (event[x] == -1)
            active--;
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

贡献在将当前线段加入活跃集合之前计算；空集贡献零；端点不重复是题目保证。
