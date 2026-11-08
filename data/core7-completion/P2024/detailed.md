## P2024 食物链

原题：[P2024](https://www.luogu.com.cn/problem/P2024)

### 从问题到算法

食物链有三种循环关系，用 x、x+n、x+2n 表示 x 所在类及循环向后的两类。统一约定“x 吃 y”对应 x 与 y+n 同类。

同类语句若发现 x 已与 y+n 或 y+2n 相连，就有矛盾；否则将三组同偏移副本合并。“x 吃 y”若发现 x 与 y 或 y+2n 同类，也有矛盾；否则合并 (x,y+n)、(x+n,y+2n)、(x+2n,y)。

编号越界，以及说自己吃自己，立即作为假话。必须先检查再合并，错误语句不能污染后续判断。并查集的等价关系完整保留所有已接受语句的传递推论。

### 复杂度

时间 O((n+k)α(n))，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    DSU d(3 * n);
    int ans = 0;
    while (k--) {
        int type, x, y;
        cin >> type >> x >> y;
        x--;
        y--;
        if (x < 0 || x >= n || y < 0 || y >= n) {
            ans++;
            continue;
        }
        if (type == 1) {
            if (d.find(x) == d.find(y + n) || d.find(x) == d.find(y + 2 * n)) {
                ans++;
                continue;
            }
            for (int j = 0; j < 3; j++)
                d.join(x + j * n, y + j * n);
        } else {
            if (d.find(x) == d.find(y) || d.find(x) == d.find(y + 2 * n)) {
                ans++;
                continue;
            }
            d.join(x, y + n);
            d.join(x + n, y + 2 * n);
            d.join(x + 2 * n, y);
        }
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

三个副本方向一致；假话不合并；编号越界也是假话。
