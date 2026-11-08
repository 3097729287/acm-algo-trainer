## P2922 Secret Message G

原题：[P2922](https://www.luogu.com.cn/problem/P2922)

### 从问题到算法

两串匹配要求它们在较短长度内完全相同，因此合法信息要么是暗号的前缀，要么以暗号为前缀。字典树恰好把这两种关系变成祖先和后代。

插入每条信息时，经过的节点的 sub 都加一，最后节点的 end 加一。查询暗号时，在每次向下一位之前，把当前节点的 end 加入答案，这些是已经结束、严格短于暗号的信息。若路径不存在，后面不再有更长匹配，但此前得到的短信息仍有效。

若整个暗号走完，加入当前节点的 sub，它包括与暗号等长以及更长的信息。祖先累加不含当前节点，所以等长信息只计一次。路径丢失后仍须把本条查询剩余输入读完。

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
