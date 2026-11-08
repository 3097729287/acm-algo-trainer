## P1328 生活大爆炸版石头剪刀布

原题：[P1328](https://www.luogu.com.cn/problem/P1328)

### 从问题到算法

五种手势规则固定，逐条分支容易漏掉某一对。建立 win[a][b]，表示手势 a 是否战胜 b；反方向表项判断乙是否得分，两者都为零就是平局。

两人的出拳序列分别循环，第 i 轮用 a[i%na]、b[i%nb]，循环周期不同也无需显式求最小公倍数。每轮从表中取甲胜、乙胜各加到对应总分。

表的行表示己方，列表示对方，填表后应检查每种手势恰好战胜两种、输给两种，且对角线全为零。

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
