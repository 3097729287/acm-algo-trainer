## P10854 Ninelie

原题：[P10854](https://www.luogu.com.cn/problem/P10854)

### 思路

令 d_i=a_i xor a_(i+1)。合法内部翻转恰好交换相邻的 01 与 10；端点翻转则删除边界。把左半边界依次移到左端、右半边界逆序移到右端，总操作数不超过 floor(n²/4)≤10^6。

### 复杂度

时间和输出量 O(n²)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, r;
    cin >> n >> r;
    vector<int> a(n);
    for (int &x : a)
        cin >> x;
    vector<int> boundary, operations;
    for (int i = 1; i < n; i++)
        if (a[i - 1] != a[i])
            boundary.push_back(i);
    for (int i : boundary)
        if (i <= n / 2)
            for (int p = i; p >= 1; p--)
                operations.push_back(p);
    for (int j = (int)boundary.size() - 1; j >= 0; j--) {
        int i = boundary[j];
        if (i > n / 2)
            for (int p = i + 1; p <= n; p++)
                operations.push_back(p);
    }
    cout << operations.size() << '\n';
    for (int p : operations)
        cout << p << ' ';
    cout << '\n';

    return 0;
}
```

### 实现提醒

保存原始边界位置；左侧从左往右处理，右侧从右往左；输出实际字符位置。
