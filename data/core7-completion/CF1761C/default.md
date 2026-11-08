## CF1761C Set Construction

原题：[CF1761C](https://www.luogu.com.cn/problem/CF1761C)

### 思路

若矩阵第 i 行第 j 列为 1，就让 j 的集合包含 i 的集合。对每个目标点沿反向边遍历，把所有能到达它的顶点编号与它自身放入集合。

### 复杂度

每组时间 O(n³)，空间 O(n²)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<string> a(n);
        for (auto &s : a)
            cin >> s;
        for (int target = 0; target < n; target++) {
            vector<char> seen(n);
            vector<int> st = {target};
            seen[target] = 1;
            while (!st.empty()) {
                int v = st.back();
                st.pop_back();
                for (int u = 0; u < n; u++)
                    if (a[u][v] == '1' && !seen[u]) {
                        seen[u] = 1;
                        st.push_back(u);
                    }
            }
            cout << count(seen.begin(), seen.end(), 1);
            for (int u = 0; u < n; u++)
                if (seen[u])
                    cout << ' ' << u + 1;
            cout << '\n';
        }
    }

    return 0;
}
```

### 实现提醒

矩阵方向不能反；每个集合包含自己的编号；输出的是集合元素。
