## CF362C Insertion Sort

原题：[CF362C](https://www.luogu.com.cn/problem/CF362C)

### 从问题到算法

交换两端后，它们自身的逆序消失，减少一。中间某值 x 若在 a[j] 与 a[i] 之间，它原来与两端形成两个逆序，交换后两个都消失，减少二；若在范围外，总逆序贡献不变。数组是排列，不存在相等边界。

原数组有可改善交换，最优必取逆序端点；枚举全部逆序对，最大化这个减少量，并统计达到最大值的端点对数。初始逆序数用平方枚举即可。

预处理 pref[i][v] 表示前 i 个位置中≤v 的元素数，用四个前缀值求中间矩形计数。n≤5000，计数最大五千，用 unsigned short 存表约五十兆字节，避免平方表浪费内存。

### 复杂度

时间 O(n²)，空间 O(n²)。

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
    for (int &x : a)
        cin >> x;
    vector<unsigned short> pref((n + 1) * n);
    for (int i = 0; i < n; i++)
        for (int v = 0; v < n; v++)
            pref[(i + 1) * n + v] = pref[i * n + v] + (a[i] <= v);
    long long inversions = 0, ways = 0;
    int best = -1;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] > a[j]) {
                inversions++;
                int high = a[i] - 1, low = a[j];
                int inside = pref[j * n + high] - pref[(i + 1) * n + high] - pref[j * n + low] +
                             pref[(i + 1) * n + low];
                int reduction = 1 + 2 * inside;
                if (reduction > best) {
                    best = reduction;
                    ways = 1;
                } else if (reduction == best)
                    ways++;
            }
    cout << inversions - best << ' ' << ways << '\n';

    return 0;
}
```

### 实现提醒

端点和数值边界都严格排除；排列从零开始；输出剩余逆序数和交换方案数。
