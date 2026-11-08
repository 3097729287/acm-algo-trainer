## P10798 消除威胁

原题：[P10798](https://www.luogu.com.cn/problem/P10798)

### 从问题到算法

一次翻转只改变符号，不能改变谁是区间绝对值的最大值。若两端的绝对值为 v，中间出现大于 v 的元素，这对端点永远不形成威胁；否则只取决于两端符号是否相同。

用绝对值单调不增的栈保存还没有遇到更大值的组。当读入 v，所有栈顶小于 v 的组都被这个更大的元素截断，可以结算；栈顶等于 v 时把当前元素计入同一组，否则建立新组。更小值不会隔断一组。

一组有 c 个非零元素，若 p 个为正，威胁数为 p(p−1)/2+(c−p)(c−p−1)/2。两种数量相差超过一时，把一个多数符号改成少数符号会减少答案，所以最优为尽量平分。v=0 时翻转仍是零，贡献 c(c−1)/2。每组的元素互不相交，可独立安排符号，故各组最小值相加就是全局最优。

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
