## P6523 加密通信

原题：[P6523](https://www.luogu.com.cn/problem/P6523)

### 从问题到算法

若 A[i]=B[i]B[i+1]、A[i+1]=B[i+1]B[i+2] 且两者不等，那么两侧质数 B[i] 与 B[i+2] 不同，故 gcd(A[i],A[i+1])=B[i+1]。这一位置唯一确定后，利用相邻乘积依次反推出所有其它质数。

题目保证忽略 M 时存在合法质数序列，且至少有两个 A 不同，因此必然能找到一对相邻不同值；无须为可能达到十八位的数做质因数分解或质性测试。

还原后若存在 B[i]>M，则唯一序列不满足限制，输出 −1；否则输出该序列。所有计算都在六十四位范围内，不要直接相乘两个十八位输入。

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
