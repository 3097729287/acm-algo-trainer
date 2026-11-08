## P1328 生活大爆炸版石头剪刀布

原题：[P1328](https://www.luogu.com.cn/problem/P1328)

### 思路

把五种手势的胜负写成固定表。第 i 轮分别使用两人序列的 i%长度 项，胜者分数加一，平局不加，累计指定轮数。

### 复杂度

时间 O(n+na+nb)，空间 O(na+nb)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, na, nb;
    cin >> n >> na >> nb;
    vector<int> a(na), b(nb);
    for (int &x : a)
        cin >> x;
    for (int &x : b)
        cin >> x;
    int win[5][5] = {
        {0, 0, 1, 1, 0}, {1, 0, 0, 1, 0}, {0, 1, 0, 0, 1}, {0, 0, 1, 0, 1}, {1, 1, 0, 0, 0}};
    int first = 0, second = 0;
    for (int i = 0; i < n; i++) {
        int x = a[i % na], y = b[i % nb];
        first += win[x][y];
        second += win[y][x];
    }
    cout << first << ' ' << second << '\n';

    return 0;
}
```

### 实现提醒

两人各自按自己的序列长度取模；平局双方都不加分。
