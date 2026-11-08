## P15267 Chaotic Time Trio

原题：[P15267](https://www.luogu.com.cn/problem/P15267)

### 从问题到算法

两个非零元素的 mex 为零，两个零的 mex 为一，一个零与一个非零的 mex 仍为非零。这些规则足以证明四元素总可成功：

零数为零时，先合并两个非零得到零，再与第三个非零合成非零，最后两个非零合成零；零数为一时先合并两个非零，得到“两零一非零”；零数为二时先合并一零一非零，得到“一零两非零”；零数为三或四时先合并两零，也归入这两种三元素可行情形。三元素中，一零两非零或两零一非零都可先合成两个非零，再合成零。

所以当元素数大于四时，任取两元素合并不会破坏最终可解性。剩至多四个时，最多只有六种首选、三种次选，直接枚举所有选择验证最终是否为零，不必硬编码小规模例外。

先记录完整操作，只有找到成功结尾后才输出；无解时只输出 −1。输出的是数值而非下标，遇到相同数也必须确实有两个副本。

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
