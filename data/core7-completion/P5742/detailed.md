## P5742 评等级

原题：[P5742](https://www.luogu.com.cn/problem/P5742)

### 从问题到算法

两条标准必须同时成立，因此使用逻辑与。第一条是严格大于一百四十，恰等于不够；第二条是大于等于八十，恰等于可以。

综合分带小数权重，可以把不等式两边同乘十，变成 7a+3b>=800，不需要浮点运算，也不必先四舍五入综合分。

每行开头的编号只标识学生，不参与成绩计算。按输入顺序为每名学生输出指定字符串 Excellent 或 Not excellent。

### 复杂度

时间 O(n)，空间 O(1)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    while (n--) {
        int id, a, b;
        cin >> id >> a >> b;
        cout << ((a + b > 140 && 7 * a + 3 * b >= 800) ? "Excellent" : "Not excellent") << '\n';
    }

    return 0;
}
```

### 实现提醒

总分严格大于 140；加权分至少 80；编号不计入成绩。
