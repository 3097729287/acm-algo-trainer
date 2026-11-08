## P1169 棋盘制作

原题：[P1169](https://www.luogu.com.cn/problem/P1169)

### 从问题到算法

合法棋盘的相邻格颜色相反，异或 (i+j)%2 后，相邻格便相同。连通矩形内所有格相同，反过来也必然还原为交替棋盘，所以可以完整转化为两个同色矩形问题。

扫描每一行，为零、一各维护每列向上连续相同颜色的高度。对一个高度直方图，递增栈在弹出高度 h 时确定它能延伸的最大宽度 w，贡献矩形面积 hw、正方形面积 min(h,w)²。

所有最大矩形都能以其中最低柱作为限制被枚举，最大正方形也能由同一跨度容纳。行尾加入零高度哨兵清空栈，最后分别输出正方形、矩形面积。

### 复杂度

时间 O(nm)，空间 O(nm+m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<int>> a(n, vector<int>(m));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            cin >> a[i][j];
            a[i][j] ^= (i + j) & 1;
        }
    long long square = 0, rectangle = 0;
    for (int color = 0; color < 2; color++) {
        vector<int> h(m + 1);
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < m; j++)
                h[j] = a[i][j] == color ? h[j] + 1 : 0;
            vector<int> st;
            for (int j = 0; j <= m; j++) {
                while (!st.empty() && h[st.back()] > h[j]) {
                    int height = h[st.back()];
                    st.pop_back();
                    int width = j - (st.empty() ? -1 : st.back()) - 1;
                    rectangle = max(rectangle, 1LL * height * width);
                    long long side = min(height, width);
                    square = max(square, side * side);
                }
                st.push_back(j);
            }
        }
    }
    cout << square << '\n' << rectangle << '\n';

    return 0;
}
```

### 实现提醒

先做行列奇偶异或；两种变换颜色都要处理；输出先正方形后矩形。
