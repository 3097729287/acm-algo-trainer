## P5744 培训

原题：[P5744](https://www.luogu.com.cn/problem/P5744)

### 思路

每个学员的姓名保留，年龄加一，成绩增加百分之二十并限制在六百分。逐条读入、计算、输出即可。

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
