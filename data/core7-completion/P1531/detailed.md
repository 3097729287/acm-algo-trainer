## P1531 I Hate It

原题：[P1531](https://www.luogu.com.cn/problem/P1531)

### 从问题到算法

一个区间的最大值等于左右两个子区间最大值中的较大者，因此可以用二叉树分治维护。叶子存一个学生的成绩，父节点存两个孩子的最大值。

修改某个成绩时，只有包含这个位置的节点会改变，从叶子一路重新计算到根。查询 [l,r] 时，完整落在范围内的节点可直接使用；其它节点继续分解。代码采用迭代线段树，把闭区间转换为左闭右开区间，左侧结果和右侧结果最终一起取最大值。

输入包含多组数据，直到文件结束。U 表示将成绩改成给定值，不是增加；Q 的两个参数是查询端点。

### 复杂度

建树 O(n)，每次操作 O(log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    while (cin >> n >> m) {
        int size = 1;
        while (size < n)
            size *= 2;
        vector<int> t(2 * size, INT_MIN);
        for (int i = 0; i < n; i++)
            cin >> t[size + i];
        for (int i = size - 1; i; i--)
            t[i] = max(t[i * 2], t[i * 2 + 1]);
        while (m--) {
            char op;
            int x, y;
            cin >> op >> x >> y;
            if (op == 'U') {
                int p = size + x - 1;
                t[p] = y;
                for (p /= 2; p; p /= 2)
                    t[p] = max(t[p * 2], t[p * 2 + 1]);
            } else {
                if (x > y)
                    swap(x, y);
                int ans = INT_MIN;
                for (int l = size + x - 1, r = size + y; l < r; l /= 2, r /= 2) {
                    if (l & 1)
                        ans = max(ans, t[l++]);
                    if (r & 1)
                        ans = max(ans, t[--r]);
                }
                cout << ans << '\n';
            }
        }
    }

    return 0;
}
```

### 实现提醒

更新是赋值；输入到 EOF；最大值查询的空段使用最小整数。
