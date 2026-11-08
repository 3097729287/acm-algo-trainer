## P14576 Lamborghini (Remix)

原题：[P14576](https://www.luogu.com.cn/problem/P14576)

### 从问题到算法

第一行开头坐标为零，长度 ai 的一行包含 ai+1 个光标位置；从它末尾到下一行开头再移动一步。因此各行末尾坐标由前缀累加 ai+1 得到，相邻末尾距离为后面那行长度加一。

同时按左右键只会给所有尚存光标加上同一个位移。要把一组光标平移进同一行，它们最大与最小坐标之差必须不超过该行长度。最长行容纳能力最强，且任意满足这个跨度的光标组都能整体平移进去，途中也不会使这些最终有效光标越界消失。

行末坐标天然递增，用双指针维护最大坐标减最小坐标不超过 max(ai) 的最长连续段。任意非连续选取都可补上中间光标而不增跨度，所以只看连续段不会漏最优。

### 复杂度

每组时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        vector<long long> position(n);
        long long current = 0, width = 0;
        for (int i = 0; i < n; i++) {
            long long x;
            cin >> x;
            width = max(width, x);
            current += x + 1;
            position[i] = current - 1;
        }
        int l = 0, ans = 0;
        for (int r = 0; r < n; r++) {
            while (position[r] - position[l] > width)
                l++;
            ans = max(ans, r - l + 1);
        }
        cout << ans << '\n';
    }

    return 0;
}
```

### 实现提醒

行间换行也占一次移动；窗口比较坐标差，不是位置数；前缀和用 long long。
