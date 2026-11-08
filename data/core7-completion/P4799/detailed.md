## P4799 世界冰球锦标赛 (Day2)

原题：[P4799](https://www.luogu.com.cn/problem/P4799)

### 从问题到算法

每件装备只有选和不选两种状态。把装备分为两半，每个完整选择唯一对应一个左半选择和一个右半选择，因此可以先生成两个价格列表，再统计符合预算的配对数。

生成列表时，从只含空集价格零的列表开始，每加入一件装备，就把原有每个价格加上它的价格形成新状态。由于所有价格非负，超过预算的状态不可能在以后恢复合法，可以直接丢弃。

右半列表排序后，固定左半价格 x，合法右半价格恰好构成不超过 M−x 的前缀，upper_bound 与 begin 的距离就是数量。不同装备组合即使价格相同，也要分别计数，所以列表不能去重。答案最多为 2⁴⁰，使用六十四位整数。空集是否购买零件均由原题的方案定义自然包含。

### 复杂度

时间 O(n·2^(n/2))，空间 O(2^(n/2))。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m;
    cin >> n >> m;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    auto generate = [&](int l, int r) {
        vector<long long> s = {0};
        for (int i = l; i < r; i++) {
            int size = s.size();
            for (int j = 0; j < size; j++)
                if (a[i] <= m - s[j])
                    s.push_back(s[j] + a[i]);
        }
        return s;
    };
    auto l = generate(0, n / 2), r = generate(n / 2, n);
    sort(r.begin(), r.end());
    long long ans = 0;
    for (long long x : l)
        ans += upper_bound(r.begin(), r.end(), m - x) - r.begin();
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

相同价格的不同子集不能去重；答案和预算都用 long long。
