## P1409 骰子

原题：[P1409](https://www.luogu.com.cn/problem/P1409)

### 从问题到算法

你不在队首时，队首掷一的情况会使别人获胜，贡献零；他离队概率为三分之一，你变成 n−1 人中第 m−1 位；他转到队尾概率二分之一，你变成同一人数中第 m−1 位。于是得到行内递推。

你在队首时，掷一立即获胜，概率六分之一；转到队尾后胜率为同一行的末项，乘二分之一；自己出队则贡献零。因此 P1=1/6+Pn/2。

将各位置写成 Pm=am·P1+bm，初始 a1=1、b1=0，am=a(m−1)/2，bm=b(m−1)/2+上一人数行的 P(m−1)/3。先算出 an、bn，得到 P1=(1/6+bn/2)/(1−an/2)，再求整行。只有一个人时按题意必胜，不能继续投骰子。

### 复杂度

时间 O(n²)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<double> previous(n + 1), current(n + 1), constant(n + 1);
    previous[1] = 1;
    for (int size = 2; size <= n; size++) {
        constant[1] = 0;
        double coefficient = 1;
        for (int position = 2; position <= size; position++) {
            coefficient *= 0.5;
            constant[position] = constant[position - 1] * 0.5 + previous[position - 1] / 3.0;
        }
        current[1] = (1.0 / 6 + constant[size] * 0.5) / (1 - coefficient * 0.5);
        for (int position = 2; position <= size; position++)
            current[position] = current[position - 1] * 0.5 + previous[position - 1] / 3.0;
        previous.swap(current);
    }
    cout << fixed << setprecision(9) << previous[m] << '\n';

    return 0;
}
```

### 实现提醒

单人胜率为 1；转队尾不减少人数；出队与轮转概率分别为 1/3 和 1/2。
