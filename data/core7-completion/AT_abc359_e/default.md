## AT_abc359_e Water Tank

原题：[AT_abc359_e](https://www.luogu.com.cn/problem/AT_abc359_e)

### 思路

第 i 项答案是 1 加上所有以 i 结尾区间的最大高度之和。用递减栈把相同最大值的后缀合并，维护每组高度和数量，新高度到来时弹掉不更高的组。

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
    vector<pair<long long, long long>> stack;
    long long sum = 0;
    for (int i = 0; i < n; i++) {
        long long h;
        cin >> h;
        long long count = 1;
        while (!stack.empty() && stack.back().first <= h) {
            auto [value, number] = stack.back();
            stack.pop_back();
            sum -= value * number;
            count += number;
        }
        stack.push_back({h, count});
        sum += h * count;
        cout << sum + 1 << (i + 1 == n ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

每个新项本身增加一个后缀；相等高度也合并；最后答案加一。
