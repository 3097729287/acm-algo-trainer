## P1414 又是毕业季II

原题：[P1414](https://www.luogu.com.cn/problem/P1414)

### 思路

若至少 k 个输入是 d 的倍数，就能选 k 个使 gcd 至少为 d。统计每个 d 的倍数出现数，把 d 更新到对应人数的答案，再按人数从大到小传播最大值。

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
