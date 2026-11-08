## CF1070C Cloud Computing

原题：[CF1070C](https://www.luogu.com.cn/problem/CF1070C)

### 思路

套餐在开始日加入、结束日次日删除。按价格维护当前可租核心数量与总费用，每天取价格最小的至多 k 个核心，用两棵树状数组做数量排名与费用前缀和。

### 复杂度

时间 O((n+m) log m)，空间 O(n+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Fenwick {
    int n;
    vector<long long> t;
    explicit Fenwick(int n) : n(n), t(n + 1) {}
    void add(int x, long long v) {
        for (; x <= n; x += x & -x)
            t[x] += v;
    }
    long long sum(int x) const {
        long long s = 0;
        for (; x; x -= x & -x)
            s += t[x];
        return s;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    long long k;
    cin >> n >> k >> m;
    struct Offer {
        int l, r, c, p;
    };
    vector<Offer> offers(m);
    vector<int> prices;
    for (auto &x : offers) {
        cin >> x.l >> x.r >> x.c >> x.p;
        prices.push_back(x.p);
    }
    sort(prices.begin(), prices.end());
    prices.erase(unique(prices.begin(), prices.end()), prices.end());
    vector<vector<pair<int, int>>> events(n + 2);
    for (auto x : offers) {
        int rank = lower_bound(prices.begin(), prices.end(), x.p) - prices.begin() + 1;
        events[x.l].push_back({rank, x.c});
        events[x.r + 1].push_back({rank, -x.c});
    }
    Fenwick count(prices.size()), cost(prices.size());
    long long total = 0, answer = 0;
    int step = 1;
    while (step <= (int)prices.size() / 2)
        step *= 2;
    for (int day = 1; day <= n; day++) {
        for (auto [rank, delta] : events[day]) {
            count.add(rank, delta);
            cost.add(rank, 1LL * delta * prices[rank - 1]);
            total += delta;
        }
        long long need = min(k, total);
        if (!need)
            continue;
        int position = 0;
        long long taken = 0;
        for (int bit = step; bit; bit /= 2) {
            int next = position + bit;
            if (next <= (int)prices.size() && taken + count.t[next] < need) {
                position = next;
                taken += count.t[next];
            }
        }
        answer += cost.sum(position) + (need - taken) * prices[position];
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

结束事件在 r+1；不足需求时租全部；数量与总费用用 long long。
