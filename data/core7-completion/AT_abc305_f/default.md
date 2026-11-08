## AT_abc305_f Dungeon Explore

原题：[AT_abc305_f](https://www.luogu.com.cn/problem/AT_abc305_f)

### 思路

到新顶点时记录父亲，优先去未访问邻点；没有新邻点就沿父边退回。每条搜索树边至多去回各一次，找到 N 前最多移动 2(N−1) 次。每次输出后刷新。

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
