## CF632D Longest Subsequence

原题：[CF632D](https://www.luogu.com.cn/problem/CF632D)

### 思路

若最小公倍数为 L，选中的数都必须整除 L，而且所有整除 L 的输入数都可以选。按倍数枚举累加频次，找到可容纳最多元素的 L，再输出所有整除它的下标。

### 复杂度

时间 O(n+m log m)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> a(n), cnt(m + 1), score(m + 1);
    for (int &x : a) {
        cin >> x;
        if (x <= m)
            cnt[x]++;
    }
    for (int v = 1; v <= m; v++)
        if (cnt[v])
            for (int L = v; L <= m; L += v)
                score[L] += cnt[v];
    int best = 1;
    for (int L = 2; L <= m; L++)
        if (score[L] > score[best])
            best = L;
    vector<int> indices;
    long long L = 1;
    for (int i = 0; i < n; i++)
        if (best % a[i] == 0) {
            indices.push_back(i + 1);
            L = L / gcd(L, (long long)a[i]) * a[i];
        }
    cout << L << ' ' << indices.size() << '\n';
    for (int i = 0; i < (int)indices.size(); i++)
        cout << indices[i] << (i + 1 == (int)indices.size() ? '\n' : ' ');
    if (indices.empty())
        cout << '\n';

    return 0;
}
```

### 实现提醒

超过 m 的数忽略；下标保持递增；空序列的 LCM 为一。
