## P5436 缘分

原题：[P5436](https://www.luogu.com.cn/problem/P5436)

### 思路

n=1 时答案为 1；否则选 n 和 n−1。它们互质，最小公倍数为 n(n−1)，且任何两个不同的合法数的乘积都不超过这个值。

### 复杂度

每组时间 O(1)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        long long n;
        cin >> n;
        cout << (n == 1 ? 1 : n * (n - 1)) << '\n';
    }

    return 0;
}
```

### 实现提醒

n=1 单独处理；乘法用六十四位。
