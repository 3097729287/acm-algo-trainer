## UVA11895 抽奖 Honorary Tickets

原题：[UVA11895](https://www.luogu.com.cn/problem/UVA11895)

### 思路

之前结果不公开，一个袋子被选 r 次后，下次中奖概率为 (l/t)((t−1)/t)^r。每个人都会选择当前概率最大的袋子，用堆取最大并更新，取第 K 次的概率。

### 复杂度

时间 O((N+K) log N)，空间 O(N)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Bag {
    long long numerator, denominator, total;
};
struct Compare {
    bool operator()(const Bag &a, const Bag &b) const {
        return (__int128)a.numerator * b.denominator < (__int128)b.numerator * a.denominator;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n, k;
        cin >> n >> k;
        priority_queue<Bag, vector<Bag>, Compare> q;
        for (int i = 0; i < n; i++) {
            long long t, l;
            cin >> t >> l;
            long long g = gcd(t, l);
            q.push({l / g, t / g, t});
        }
        for (int step = 1; step < k; step++) {
            Bag b = q.top();
            q.pop();
            long long a = b.total - 1, d = b.total, g = gcd(a, b.denominator);
            a /= g;
            b.denominator /= g;
            g = gcd(d, b.numerator);
            d /= g;
            b.numerator /= g;
            b.numerator *= a;
            b.denominator *= d;
            if (!b.numerator)
                b.denominator = 1;
            q.push(b);
        }
        auto b = q.top();
        long long g = gcd(b.numerator, b.denominator);
        cout << b.numerator / g << '/' << b.denominator / g << '\n';
    }

    return 0;
}
```

### 实现提醒

信封放回但奖票不放回；前面结果不可见；比较分数用宽整数；最后约分输出。
