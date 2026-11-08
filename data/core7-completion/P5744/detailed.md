## P5744 培训

原题：[P5744](https://www.luogu.com.cn/problem/P5744)

### 从问题到算法

每条记录之间没有相互影响，可以边读边处理。年龄用原值加一，成绩的新值是原来的十二成，不能把“增加百分之二十”误写成只取两成。

输入成绩为整数且输出也要求整数，可写 score*12/10，先乘再整除，最后与六百取最小值。这样避免浮点数乘 1.2 在整数边界附近出现细小误差。姓名按完整字符串原样输出。

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
        string name;
        int age, score;
        cin >> name >> age >> score;
        cout << name << ' ' << age + 1 << ' ' << min(600, score * 12 / 10) << '\n';
    }

    return 0;
}
```

### 实现提醒

先乘十二再除十；成绩最多六百；每名学员年龄加一。
