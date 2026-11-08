## P1334 瑞瑞的木板

原题：[P1334](https://www.luogu.com.cn/problem/P1334)

### 思路

把所有木板长度放进小根堆，每次取最小两段合并，付出长度和并将新段放回。重复至只剩一段，累计费用。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    priority_queue<long long, vector<long long>, greater<long long>> q;
    while (n--) {
        long long x;
        cin >> x;
        q.push(x);
    }
    long long answer = 0;
    while (q.size() > 1) {
        long long a = q.top();
        q.pop();
        long long b = q.top();
        q.pop();
        answer += a + b;
        q.push(a + b);
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

每次取当前最短两段；合并结果重新入堆；总费用用 long long。
