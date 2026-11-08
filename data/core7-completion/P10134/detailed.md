## P10134 Cowmpetency S

原题：[P10134](https://www.luogu.com.cn/problem/P10134)

### 从问题到算法

对记忆 (a,h)，条件等价于 max(c1..ca)=max(c1..c[h−1])，且 c[h] 严格更大。相同 h 只需保留最小 a；区间 a+1..h−1 中都不能产生新前缀纪录，而 h 必须产生纪录。必创纪录点落在禁创区间时立即矛盾。

未知值先置一，保留“原本未知且不禁止创纪录”的位置有序集合。按 h 递增处理，设 a 前最大值为 M，中间 a+1..h−1 最大值为 need。若 need>M，必须在一到 a 抬高一个原未知位置；为了字典序最小，选择可行的最右位置并只抬到 need。禁创纪录位置不能用，因为抬到超过 M 必然违反已有纪录约束。

之后 h 若未知，设为此前最大值加一；若已知，就检查是否已经严格更大。线段树支持区间最大值和单点抬高。后来的被迫抬高若破坏早先固定纪录，完整复核会发现矛盾；最右可改位置已涵盖所有更晚可用纪录点，换更早位置不能避开这种矛盾。

最终检查所有原记忆与 C 上限。每个抬高都是由不可更改的中间值或必须出现的新纪录强制，且总选最晚位置、最小必要值，所以可行时得到字典序最小序列。

### 复杂度

时间 O((N+Q) log N)，空间 O(N+Q)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n, q;
        long long C;
        cin >> n >> q >> C;
        vector<long long> a(n + 1), original(n + 1);
        for (int i = 1; i <= n; i++) {
            cin >> original[i];
            a[i] = original[i] ? original[i] : 1;
        }
        vector<pair<int, int>> constraints(q);
        vector<int> first(n + 1, n + 1), diff(n + 3);
        for (auto &[l, h] : constraints) {
            cin >> l >> h;
            first[h] = min(first[h], l);
        }
        for (int h = 1; h <= n; h++)
            if (first[h] <= n) {
                diff[first[h] + 1]++;
                diff[h]--;
            }
        vector<char> forbidden(n + 1);
        int active = 0;
        bool ok = true;
        set<int> changeable;
        for (int i = 1; i <= n; i++) {
            active += diff[i];
            forbidden[i] = active > 0;
            if (first[i] <= n && forbidden[i])
                ok = false;
            if (!original[i] && !forbidden[i])
                changeable.insert(i);
        }
        int size = 1;
        while (size < n)
            size *= 2;
        vector<long long> tree(2 * size);
        for (int i = 1; i <= n; i++)
            tree[size + i - 1] = a[i];
        for (int i = size - 1; i; i--)
            tree[i] = max(tree[i * 2], tree[i * 2 + 1]);
        auto query = [&](int l, int r) {
            long long ans = 0;
            for (l += size - 1, r += size; l < r; l /= 2, r /= 2) {
                if (l & 1)
                    ans = max(ans, tree[l++]);
                if (r & 1)
                    ans = max(ans, tree[--r]);
            }
            return ans;
        };
        auto setValue = [&](int i, long long value) {
            a[i] = value;
            int p = size + i - 1;
            tree[p] = value;
            for (p /= 2; p; p /= 2)
                tree[p] = max(tree[p * 2], tree[p * 2 + 1]);
        };
        for (int h = 1; h <= n && ok; h++)
            if (first[h] <= n) {
                int l = first[h];
                long long before = query(1, l), need = query(l + 1, h - 1);
                if (need > before) {
                    auto it = changeable.upper_bound(l);
                    if (it == changeable.begin()) {
                        ok = false;
                        break;
                    }
                    --it;
                    setValue(*it, need);
                }
                long long maximum = query(1, h - 1);
                if (!original[h])
                    setValue(h, maximum + 1);
                else if (a[h] <= maximum)
                    ok = false;
            }
        for (int i = 1; i <= n; i++)
            if (a[i] > C)
                ok = false;
        for (auto [l, h] : constraints)
            if (query(1, l) != query(1, h - 1) || a[h] <= query(1, l))
                ok = false;
        if (!ok)
            cout << -1 << '\n';
        else
            for (int i = 1; i <= n; i++)
                cout << a[i] << (i == n ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

相同 h 取最小 a；原已知值不能改；最终复核全部记忆和数值上限。
