## AT_abc305_f Dungeon Explore

原题：[AT_abc305_f](https://www.luogu.com.cn/problem/AT_abc305_f)

### 从问题到算法

这道题没有一次性给出全部边，程序必须在每次移动前读取当前邻居。维护已访问标记与 DFS 父亲：有未访问邻点就前往并标记，没有则回父亲，回到父亲后重新读取它的邻居再继续。

连通图中，若还没到 N 就不可能在根也无路可走，否则所有可达点都已访问而遗漏 N，矛盾。每次前往未访问点新增一条搜索树边，之后最多退回一次，所以总移动不超过 2(N−1)，满足 2N 限制。这一论证只使用已经揭示的信息，也适用于原题的自适应评测。

读取字符串形式的首个反馈，遇到 OK 或 −1 立即结束，否则把它当作邻居数量。输出邻点用 endl 刷新缓冲，不能拿普通离线输入样例替代交互验证；本参考程序通过本地邻居反馈评测器核验移动合法性与次数。

### 复杂度

读取邻居总时间 O(N+M)，移动次数 O(N)，空间 O(N)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    if (!(cin >> n >> m))
        return 0;
    vector<int> parent(n + 1);
    vector<char> seen(n + 1);
    int current = 1;
    seen[1] = 1;
    for (;;) {
        string token;
        if (!(cin >> token))
            return 0;
        if (token == "OK" || token == "-1")
            return 0;
        int k = stoi(token), next = 0;
        for (int i = 0; i < k; i++) {
            int v;
            cin >> v;
            if (!seen[v])
                next = v;
        }
        if (next) {
            parent[next] = current;
            seen[next] = 1;
        } else
            next = parent[current];
        if (!next)
            return 0;
        cout << next << endl;
        current = next;
    }

    return 0;
}
```

### 实现提醒

每次反馈都要完整读完；收到 OK/−1 立即结束；输出后 flush。
