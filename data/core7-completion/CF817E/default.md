## CF817E Choosing The Commander

原题：[CF817E](https://www.luogu.com.cn/problem/CF817E)

### 思路

字典树每个节点记录当前有多少数经过。查询 x xor y<p 时逐位比较：p 当前位为一，可把异或位为零的整支加入答案，再沿异或位为一的分支继续；p 位为零时只能沿同位。

### 复杂度

每次操作 O(log W)，空间 O(插入次数·log W)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Node {
    int child[2] = {0, 0}, count = 0;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int q;
    cin >> q;
    vector<Node> t(1);
    while (q--) {
        int op, x;
        cin >> op >> x;
        if (op < 3) {
            int v = 0, delta = op == 1 ? 1 : -1;
            t[v].count += delta;
            for (int b = 30; b >= 0; b--) {
                int bit = (x >> b) & 1;
                if (!t[v].child[bit]) {
                    t[v].child[bit] = t.size();
                    t.push_back(Node());
                }
                v = t[v].child[bit];
                t[v].count += delta;
            }
        } else {
            int p;
            cin >> p;
            int v = 0, ans = 0;
            for (int b = 30; b >= 0; b--) {
                int bit = (x >> b) & 1;
                if ((p >> b) & 1) {
                    int same = t[v].child[bit];
                    if (same)
                        ans += t[same].count;
                    v = t[v].child[bit ^ 1];
                } else
                    v = t[v].child[bit];
                if (!v)
                    break;
            }
            cout << ans << '\n';
        }
    }

    return 0;
}
```

### 实现提醒

条件是严格小于；允许重复值；删除更新整条路径计数。
