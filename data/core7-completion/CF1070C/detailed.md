## CF1070C Cloud Computing

原题：[CF1070C](https://www.luogu.com.cn/problem/CF1070C)

### 从问题到算法

不同天的租赁决定互不影响，所以每天只需选择当天最便宜的 k 个核心；不足 k 个时全部租下。套餐中每个核心价格相同，可以把容量看成该价格的重复次数。

把套餐转成两个事件：l 日增加 c 个价格 p 的核心，r+1 日删除 c 个。价格离散化后，用第一棵树状数组保存数量，第二棵保存数量乘价格。

每天处理完事件，令 need=min(k,总数量)。在数量树上二进制提升，找第 need 个核心所在价格。更低价格全部买入，费用用前缀和取得；剩余 need−低价数量 个按临界价格购买。一个套餐只产生两次点更新，不能把每个核心展开存储。

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
