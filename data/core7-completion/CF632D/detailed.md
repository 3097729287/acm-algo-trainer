## CF632D Longest Subsequence

原题：[CF632D](https://www.luogu.com.cn/problem/CF632D)

### 从问题到算法

任何 LCM≤m 的子序列，必然包含在“所有能整除该 LCM 的输入元素”中，补上这些元素不会让 LCM 超出 L。因此只要对每个 L≤m 计算输入中有多少个 L 的因数。

统计 cnt[v] 后，枚举每个 v≤m，把 cnt[v] 加到所有倍数 v、2v、3v……的得分。得分最大的候选 L 对应最优长度；大于 m 的输入数无法加入任何合法非空子序列，可直接略过。

输出这些元素的下标，并实际累积它们的 LCM 作为输出值，保证输出与子序列完全一致。若一个都选不到，空序列的 LCM 按题意为一。

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
