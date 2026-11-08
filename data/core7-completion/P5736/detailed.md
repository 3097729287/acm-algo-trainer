## P5736 质数筛

原题：[P5736](https://www.luogu.com.cn/problem/P5736)

### 从问题到算法

如果合数 x=a·b 的两个因子都大于 sqrt(x)，乘积就会大于 x，矛盾。因此一个合数一定有不超过平方根的非平凡因子。

先排除 x<2，再枚举 d，只要 d<=x/d 就继续；若 x%d==0，则为合数。使用 d<=x/d 能避免 d*d 的溢出。枚举结束没有因子，就是质数。

逐个处理、只输出质数，原输入顺序和重复出现次数都保留，不要把题名中的筛字理解为必须对答案排序去重。

### 复杂度

时间 O(n sqrt A)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    bool first = true;
    while (n--) {
        long long x;
        cin >> x;
        bool prime = x >= 2;
        for (long long d = 2; prime && d <= x / d; d++)
            if (x % d == 0)
                prime = false;
        if (prime) {
            if (!first)
                cout << ' ';
            first = false;
            cout << x;
        }
    }
    cout << '\n';

    return 0;
}
```

### 实现提醒

1 不是质数；保留顺序与重复；平方根条件避免乘法溢出。
