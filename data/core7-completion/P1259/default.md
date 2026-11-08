## P1259 黑白棋子的移动

原题：[P1259](https://www.luogu.com.cn/problem/P1259)

### 思路

n>4 时，把中间的白黑一对移到末尾空位，再用右端两黑补上空位，就留下 n−1 对的同类问题，末尾多一对白黑。递归至四对后使用五步固定收尾。

这里逐帧重放四对棋子的固定收尾，编号与代码中的 move 参数一致。空位用绿色标出，前后完整状态可以暂停核对。

![四对棋子的五步收尾](assets/paired-pieces.svg)

### 复杂度

共有 O(n) 次移动，输出长度 O(n)，总时间 O(n²)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    string a(n, 'o');
    a += string(n, '*');
    a += "--";
    cout << a << '\n';
    auto move = [&](int from, int to) {
        from--;
        to--;
        swap(a[from], a[to]);
        swap(a[from + 1], a[to + 1]);
        cout << a << '\n';
    };
    function<void(int)> solve = [&](int k) {
        if (k == 4) {
            move(4, 9);
            move(8, 4);
            move(2, 8);
            move(7, 2);
            move(1, 7);
            return;
        }
        move(k, 2 * k + 1);
        move(2 * k - 1, k);
        solve(k - 1);
    };
    solve(n);

    return 0;
}
```

### 实现提醒

先打印初始状态；移动一对的左右顺序不变；递归只处理前缀。
