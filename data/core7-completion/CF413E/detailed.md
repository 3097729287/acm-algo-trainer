## CF413E Maze 2D

原题：[CF413E](https://www.luogu.com.cn/problem/CF413E)

### 从问题到算法

对起终列之间的矩形，最短路不需要跑到更外侧：若从边界一行出发绕到外侧再回另一行，两边界格都可走，可以用边界上的一条竖边替代并缩短。因此只需查询这两列之间。

两行图的一个竖直切口只有两条横边。无重复顶点的最短路从切口左侧到右侧，跨过切口的次数必须为奇数，又不可能重复使用边，所以只跨一次。于是合并距离为 min_r(left[a][r]+1+right[r][b])。障碍对应无穷距离。

单列同格距离零，两格都开放时跨行距离一。线段树合并按从左到右的顺序，不能交换查询两侧累计矩阵。编号先拆成行与列，必要时交换起终点使起始列较小。

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
