## P2325 王室联邦

原题：[P2325](https://www.luogu.com.cn/problem/P2325)

### 思路

后序遍历中把尚未归省的点留在栈上。处理一个孩子后，若当前根累计的待分配点不少于 B，就把这一段整体划为一省，以当前根为省会。最后剩余点并入最后一省。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, B;
    cin >> n >> B;
    vector<vector<int>> g(n);
    for (int i = 1; i < n; i++) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        g[a].push_back(b);
        g[b].push_back(a);
    }
    vector<int> st, belong(n), capitals;
    function<void(int, int)> dfs = [&](int v, int p) {
        int base = st.size();
        for (int u : g[v])
            if (u != p) {
                dfs(u, v);
                if ((int)st.size() - base >= B) {
                    capitals.push_back(v);
                    int id = capitals.size();
                    while ((int)st.size() > base) {
                        belong[st.back()] = id;
                        st.pop_back();
                    }
                }
            }
        st.push_back(v);
    };
    dfs(0, -1);
    if (capitals.empty())
        capitals.push_back(0);
    for (int v : st)
        belong[v] = capitals.size();
    cout << capitals.size() << '\n';
    for (int i = 0; i < n; i++)
        cout << belong[i] << (i + 1 == n ? '\n' : ' ');
    for (int i = 0; i < (int)capitals.size(); i++)
        cout << capitals[i] + 1 << (i + 1 == (int)capitals.size() ? '\n' : ' ');

    return 0;
}
```

### 实现提醒

省会可以在省外；只弹当前根积累的栈段；末尾剩余不能独立形成过小省。
