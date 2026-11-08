## CF888E Maximum Subsequence

原题：[CF888E](https://www.luogu.com.cn/problem/CF888E)

### 从问题到算法

三十五个元素不能枚举全部 2³⁵ 个子集，但分成两半后，各自只有约 2¹⁸ 个子集。每个完整子集唯一拆成一个左半子集和一个右半子集。

两半的和都先对 m 取余，结果为 x、y。若 x+y<m，答案就是 x+y；若回绕，结果为 x+y−m，它不超过 x 或 y 中任一非负较大者，而另一半取空集时已经能够得到单半余数。因此全局最优一定可由一对不回绕的余数达到。

排序右半列表。对每个 x，用 upper_bound 找第一个大于 m−1−x 的元素，向前一步就得到允许范围内的最大 y。空子集提供余数零，所以始终存在可选值。余数与加法使用 long long，避免两个接近模数的数相加溢出 int。

### 复杂度

时间 O(2^(n/2)·n)，空间 O(2^(n/2))。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long mod;
    cin >> n >> mod;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    auto enumerate = [&](int l, int r) {
        vector<long long> s = {0};
        for (int i = l; i < r; i++) {
            int z = s.size();
            for (int j = 0; j < z; j++)
                s.push_back((s[j] + a[i]) % mod);
        }
        return s;
    };
    auto l = enumerate(0, n / 2), r = enumerate(n / 2, n);
    sort(r.begin(), r.end());
    long long ans = 0;
    for (long long x : l) {
        auto it = upper_bound(r.begin(), r.end(), mod - 1 - x);
        if (it != r.begin())
            ans = max(ans, x + *prev(it));
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

两半都包含空集；先取余；upper_bound 返回位置，取前驱前检查边界。
