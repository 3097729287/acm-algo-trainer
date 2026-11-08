## P15267 Chaotic Time Trio

原题：[P15267](https://www.luogu.com.cn/problem/P15267)

### 思路

任意四元素集合都能最终合为零。因此先任意合并直到只剩四个，再穷举这四个的所有合并次序。初始不足四个也直接穷举，并按真实元素值输出每次选择。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        deque<long long> values;
        for (int i = 0; i < n; i++) {
            long long x;
            cin >> x;
            values.push_back(x);
        }
        vector<pair<long long, long long>> operations;
        auto mex = [](long long a, long long b) {
            for (int v = 0;; v++)
                if (v != a && v != b)
                    return (long long)v;
        };
        while (values.size() > 4) {
            long long a = values.front();
            values.pop_front();
            long long b = values.front();
            values.pop_front();
            operations.push_back({a, b});
            values.push_back(mex(a, b));
        }
        vector<long long> small(values.begin(), values.end());
        function<bool(vector<long long>)> solve = [&](vector<long long> a) {
            if (a.size() == 1)
                return a[0] == 0;
            for (int i = 0; i < (int)a.size(); i++)
                for (int j = i + 1; j < (int)a.size(); j++) {
                    vector<long long> next;
                    for (int k = 0; k < (int)a.size(); k++)
                        if (k != i && k != j)
                            next.push_back(a[k]);
                    next.push_back(mex(a[i], a[j]));
                    operations.push_back({a[i], a[j]});
                    if (solve(next))
                        return true;
                    operations.pop_back();
                }
            return false;
        };
        if (!solve(small))
            cout << -1 << '\n';
        else {
            for (auto [a, b] : operations)
                cout << a << ' ' << b << '\n';
            if (n == 1)
                cout << '\n';
        }
    }

    return 0;
}
```

### 实现提醒

mex 只需检查 0、1、2；操作输出数值；成功时恰好 n−1 次；无解前不输出半成品。
