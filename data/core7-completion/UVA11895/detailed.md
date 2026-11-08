## UVA11895 抽奖 Honorary Tickets

原题：[UVA11895](https://www.luogu.com.cn/problem/UVA11895)

### 从问题到算法

每个袋子始终保留 t 个信封，中奖后只是拿走奖票，空信封仍放回。对其中一张初始奖票，它在前 r 次抽取中没有被抽中的概率为 ((t−1)/t)^r，所以剩余奖票期望为 l 乘这个值，下次中奖概率再除以 t。

前面学生的结果不公开，后续学生不能根据具体中奖结果更新袋子，只能根据它已被抽了多少次计算上述无条件概率。每人为了最大化自己的中奖概率，都会选当前概率最大者；抽一次后，该袋子概率乘 (t−1)/t。

把各袋概率放进最大堆，重复 K−1 次取顶并更新，第 K 次堆顶就是答案。用约分后的有理数保存概率，比较用 __int128 交叉相乘，避免接近概率的浮点误排。更新先交叉约分，再相乘。题目保证本人与所有前驱实际选中的概率分子分母都在 32 位范围，更新后的候选使用六十四位保存。

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
