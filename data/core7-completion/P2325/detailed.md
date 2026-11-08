## P2325 王室联邦

原题：[P2325](https://www.luogu.com.cn/problem/P2325)

### 从问题到算法

每个孩子返回时未分配的部分少于或等于 B；在当前根下累计未分配点，达到 B 就立即切出。切出前累计不足 B，加上一个孩子剩余最多 B，因此新省大小不超过 2B−1。

这些点到当前根的路径，除省会本身外都处在本次切出的栈段内，所以满足省会可在省外的路径条件。当前根随后也留在未分配栈中，可以作为多个省的省会。

最后根返回的剩余最多 B 个点，并入最后一省后大小不超过 3B−1，连接路径也都在该省或省会中。若从未切出省，全部 n 个点一起为一省；此时由算法可知 n≤B，结合题设 B≤n，恰为 B。

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
