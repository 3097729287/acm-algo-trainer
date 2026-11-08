## CF362C Insertion Sort

原题：[CF362C](https://www.luogu.com.cn/problem/CF362C)

### 思路

插入排序交换次数就是逆序对数。交换 i<j 且 a[i]>a[j] 会减少 1+2·count 个逆序，其中 count 是中间位置且值严格夹在两端之间的元素数。二维前缀计数使每对查询为常数时间。

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
