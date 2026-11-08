## P5426 Balancing Inversions G

原题：[P5426](https://www.luogu.com.cn/problem/P5426)

### 思路

不跨中线时用两半逆序数差的绝对值补齐。跨中线只需考虑同一方向，把左侧最靠右的一类字符与右侧最靠左的另一类字符依次交换，维护必要代价和新的逆序差。

样例中把中线的 01 换成 10，只需一次交换便使两半逆序数相等。跨中线操作可能同时改变两侧逆序数，计算时使用推导的固定差值。

![跨中线交换对逆序差的影响](assets/central-inversion-swap.svg)

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(2 * n);
    int ones = 0;
    for (int &x : a) {
        cin >> x;
        ones += x;
    }
    auto inversions = [&](int l, int r) {
        long long count = 0, answer = 0;
        for (int i = l; i < r; i++)
            if (a[i])
                count++;
            else
                answer += count;
        return answer;
    };
    long long initial = inversions(0, n) - inversions(n, 2 * n), ans = llabs(initial);
    for (int bit = 0; bit < 2; bit++) {
        vector<int> left, right;
        for (int i = n - 1; i >= 0; i--)
            if (a[i] == bit)
                left.push_back(i);
        for (int i = 0; i < n; i++)
            if (a[n + i] != bit)
                right.push_back(i);
        long long delta = initial, cost = 0;
        int sign = bit ? 1 : -1;
        for (int i = 0; i < (int)min(left.size(), right.size()); i++) {
            long long q = left[i], z = right[i];
            cost += n - q + z;
            delta += sign * (q + z - 2 * n + 1 + ones);
            ans = min(ans, cost + llabs(delta));
        }
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

z 使用右半局部下标；两种跨线方向均枚举；代价和逆序差用 long long。
