## CF413E Maze 2D

原题：[CF413E](https://www.luogu.com.cn/problem/CF413E)

### 思路

每段保存左边界两格到右边界两格的四个最短距离。相邻段通过上、下两种边界横边连接，枚举跨边所在行合并。查询两点列区间得到对应矩阵项。

### 复杂度

预处理 O(n)，每问 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

const int INF = 100000000;
struct Matrix {
    bool valid = false;
    int d[2][2] = {{INF, INF}, {INF, INF}};
};
Matrix mergeMatrix(const Matrix &a, const Matrix &b) {
    if (!a.valid)
        return b;
    if (!b.valid)
        return a;
    Matrix c;
    c.valid = true;
    for (int i = 0; i < 2; i++)
        for (int j = 0; j < 2; j++)
            for (int r = 0; r < 2; r++)
                c.d[i][j] = min(c.d[i][j], a.d[i][r] + 1 + b.d[r][j]);
    return c;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    string s[2];
    cin >> s[0] >> s[1];
    int size = 1;
    while (size < n)
        size *= 2;
    vector<Matrix> tree(2 * size);
    for (int i = 0; i < n; i++) {
        auto &v = tree[size + i];
        v.valid = true;
        for (int a = 0; a < 2; a++)
            for (int b = 0; b < 2; b++)
                v.d[a][b] = s[a][i] == '.' && s[b][i] == '.' ? (a == b ? 0 : 1) : INF;
    }
    for (int i = size - 1; i >= 1; i--)
        tree[i] = mergeMatrix(tree[2 * i], tree[2 * i + 1]);
    auto query = [&](int l, int r) {
        Matrix left, right;
        for (l += size, r += size; l < r; l /= 2, r /= 2) {
            if (l & 1)
                left = mergeMatrix(left, tree[l++]);
            if (r & 1)
                right = mergeMatrix(tree[--r], right);
        }
        return mergeMatrix(left, right);
    };
    while (q--) {
        int a, b;
        cin >> a >> b;
        a--;
        b--;
        int ra = a / n, ca = a % n, rb = b / n, cb = b % n;
        if (ca > cb) {
            swap(ca, cb);
            swap(ra, rb);
        }
        int ans = query(ca, cb + 1).d[ra][rb];
        cout << (ans >= INF ? -1 : ans) << '\n';
    }

    return 0;
}
```

### 实现提醒

矩阵合并有顺序；同列可以直接走竖边；不可达输出 −1。
