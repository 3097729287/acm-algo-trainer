## P1414 又是毕业季II

原题：[P1414](https://www.luogu.com.cn/problem/P1414)

### 从问题到算法

某 k 个数的 gcd 为 g，就说明这 k 个数全是 g 的倍数；反过来，若 d 的倍数至少有 k 个，任选 k 个后 gcd 至少为 d。因此最大可能 gcd 就是满足倍数数量不少于 k 的最大 d。

先统计原值频数，然后枚举 d 的所有倍数累加，得到 cnt[d]。把 d 放到 answer[cnt[d]]，表示至少这么多人可以共享这个公因子。因为能选更多人时也能只选其中 k 人，人数从大到小做后缀最大值即可得到每个 k 的答案。

重复数对应不同学生，按频数累加。无需枚举学生子集，也不必判断选出的数 gcd 是否恰好为 d，因为我们取所有可行 d 的最大值。

### 复杂度

时间 O(A log A+n)，空间 O(A+n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int limit = 0;
    for (int &x : a) {
        cin >> x;
        limit = max(limit, x);
    }
    vector<int> frequency(limit + 1), answer(n + 2);
    for (int x : a)
        frequency[x]++;
    for (int d = 1; d <= limit; d++) {
        int c = 0;
        for (int j = d; j <= limit; j += d)
            c += frequency[j];
        if (c)
            answer[c] = max(answer[c], d);
    }
    for (int k = n - 1; k >= 1; k--)
        answer[k] = max(answer[k], answer[k + 1]);
    for (int k = 1; k <= n; k++)
        cout << answer[k] << '\n';

    return 0;
}
```

### 实现提醒

按次数统计；答案对人数做后缀最大值；k 从 1 到 n 输出。
