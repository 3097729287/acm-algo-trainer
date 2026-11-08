## CF817E Choosing The Commander

原题：[CF817E](https://www.luogu.com.cn/problem/CF817E)

### 从问题到算法

比较二进制整数时，第一次不同的高位决定大小。查询过程中，当前路径对应的异或前缀始终与 p 相同。若 p 当前位为一，把异或位设零就已严格更小，后面任意取值，因此整支数量直接加入答案；继续搜索的另一支则保持当前位相同。若 p 当前位为零，只能令异或位为零。

插入和删除都沿完整数值路径更新经过计数，重复值分别累计。删除只把计数减一，不必物理回收节点，查询遇到计数为零的分支自然无贡献。

扫描完全部位仍相等的数不能计入，因为条件是严格小于 p。p=0 时自然返回零。

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
