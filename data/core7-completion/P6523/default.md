## P6523 加密通信

原题：[P6523](https://www.luogu.com.cn/problem/P6523)

### 思路

找到一对不同的相邻 A，它们的 gcd 恰好是共同的中间质数。以此向左右逐项相除还原全部 B，最后检查是否均不超过 M。

### 复杂度

时间 O(n+log max A)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n;
        long long M;
        cin >> n >> M;
        vector<long long> a(n - 1), b(n);
        for (auto &x : a)
            cin >> x;
        int k = 0;
        while (a[k] == a[k + 1])
            k++;
        b[k + 1] = gcd(a[k], a[k + 1]);
        for (int i = k; i >= 0; i--)
            b[i] = a[i] / b[i + 1];
        for (int i = k + 1; i < n - 1; i++)
            b[i + 1] = a[i] / b[i];
        bool ok = all_of(b.begin(), b.end(), [&](long long x) { return x <= M; });
        if (!ok)
            cout << -1 << '\n';
        else
            for (int i = 0; i < n; i++)
                cout << b[i] << (i + 1 == n ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

使用相邻且不同的乘积；gcd 对应中间位置；依赖题目保证的质数分解存在性。
