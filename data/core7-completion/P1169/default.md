## P1169 棋盘制作

原题：[P1169](https://www.luogu.com.cn/problem/P1169)

### 思路

将每格颜色异或行列奇偶，交替棋盘就变成全零或全一矩形。分别维护两种颜色的直方图高度，用单调栈求最大矩形，并以 min(高,宽) 求最大正方形。

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
