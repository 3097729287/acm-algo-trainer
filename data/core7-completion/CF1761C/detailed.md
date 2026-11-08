## CF1761C Set Construction

原题：[CF1761C](https://www.luogu.com.cn/problem/CF1761C)

### 从问题到算法

给第 i 个集合放入一个专属于它的编号 i。如果图中有从 i 到 j 的路径，子集关系的传递性要求 i 的编号也出现在 j 的集合中。因此可以令第 j 个集合恰好包含所有能到达 j 的顶点。

对每个 j，从 j 沿反向边搜索，访问到的编号就是答案。存在 i→j 时，i 的每个祖先也能到达 j，所以构造满足包含关系。原题保证可构造且对应关系允许这种偏序构造，不会要求相互严格包含。

矩阵大小至多一百，直接为每个顶点做一次遍历即可。输出集合大小和实际编号，不需要枚举整数子集。

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
