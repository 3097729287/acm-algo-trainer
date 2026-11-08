## P3988 发牌

原题：[P3988](https://www.luogu.com.cn/problem/P3988)

### 从问题到算法

每次把牌顶移到底只改变循环起点，不改变剩余牌的相对顺序。若剩余 remain 张、当前零开始排名为 rank，销 R 次后的发牌排名为 (rank+R)%remain。

每个编号存一表示尚未发出，树状数组维护前缀存活数量。用倍增查找前缀和首次达到 rank+1 的位置，就是这一张的原编号。删除后，它的下一张在新序列中仍占据同一个 rank；若刚删除末尾，下次取模自然回到零。

初始全为一，Fenwick 的每项可直接初始化为 lowbit(i)，避免逐点建立。

### 复杂度

时间 O(N log N)，空间 O(N)。

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

    int n;
    cin >> n;
    Fenwick bit(n);
    for (int i = 1; i <= n; i++)
        bit.t[i] = i & -i;
    long long rank = 0;
    int highest = 1;
    while ((highest << 1) <= n)
        highest <<= 1;
    for (int remain = n; remain >= 1; remain--) {
        long long R;
        cin >> R;
        rank = (rank + R) % remain;
        long long need = rank + 1;
        int pos = 0;
        for (int step = highest; step; step >>= 1) {
            int next = pos + step;
            if (next <= n && bit.t[next] < need) {
                need -= bit.t[next];
                pos = next;
            }
        }
        int card = pos + 1;
        cout << card << '\n';
        bit.add(card, -1);
    }

    return 0;
}
```

### 实现提醒

排名按剩余牌数取模；删除后起点是下一张；输出原牌号。
