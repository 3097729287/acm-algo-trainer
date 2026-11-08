## P10798 消除威胁

原题：[P10798](https://www.luogu.com.cn/problem/P10798)

### 思路

绝对值无法改变。对每个绝对值，只在中间没有更大绝对值的同值元素间形成威胁。这些元素形成独立组，非零组把正负数量尽量平分；零不能变号，组内任意两点都贡献一次。

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
    vector<pair<long long, long long>> st;
    long long ans = 0;
    auto settle = [&]() {
        auto [v, c] = st.back();
        st.pop_back();
        if (v == 0)
            ans += c * (c - 1) / 2;
        else {
            long long a = c / 2, b = c - a;
            ans += a * (a - 1) / 2 + b * (b - 1) / 2;
        }
    };
    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;
        x = llabs(x);
        while (!st.empty() && st.back().first < x)
            settle();
        if (!st.empty() && st.back().first == x)
            st.back().second++;
        else
            st.push_back({x, 1});
    }
    while (!st.empty())
        settle();
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

0 无法改变符号；只在遇到严格更大绝对值时结算小组；答案用 long long。
