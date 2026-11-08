## P2922 Secret Message G

原题：[P2922](https://www.luogu.com.cn/problem/P2922)

### 思路

把拦截到的信息插入二进制字典树。对每条暗号，沿路径累加严格祖先的结束次数，走到末端后再加整棵子树的信息数，即覆盖信息更短和信息不短于暗号的两种情况。

### 复杂度

时间 O(输入总位数)，空间 O(拦截信息总位数)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

struct Node {
    int child[2] = {0, 0};
    int sub = 0, end = 0;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int m, n;
    cin >> m >> n;
    vector<Node> t(1);
    for (int i = 0; i < m; i++) {
        int len;
        cin >> len;
        int v = 0;
        t[v].sub++;
        while (len--) {
            int b;
            cin >> b;
            if (!t[v].child[b]) {
                t[v].child[b] = t.size();
                t.push_back(Node());
            }
            v = t[v].child[b];
            t[v].sub++;
        }
        t[v].end++;
    }
    while (n--) {
        int len;
        cin >> len;
        int v = 0, ans = 0;
        bool alive = true;
        while (len--) {
            int b;
            cin >> b;
            if (alive) {
                ans += t[v].end;
                int next = t[v].child[b];
                if (!next)
                    alive = false;
                else
                    v = next;
            }
        }
        if (alive)
            ans += t[v].sub;
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

同一信息可能重复，应按次数计；等长匹配不重复；失败后继续读取剩余位。
