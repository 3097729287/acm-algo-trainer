## P5740 最厉害的学生

原题：[P5740](https://www.luogu.com.cn/problem/P5740)

### 思路

对每个学生求三科总分，仅在总分严格大于当前最高值时替换答案。这样并列时保留先输入的学生，最后输出姓名和三科原成绩。

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
    string name;
    int x = 0, y = 0, z = 0, best = -1;
    while (n--) {
        string s;
        int a, b, c;
        cin >> s >> a >> b >> c;
        if (a + b + c > best) {
            best = a + b + c;
            name = s;
            x = a;
            y = b;
            z = c;
        }
    }
    cout << name << ' ' << x << ' ' << y << ' ' << z << '\n';

    return 0;
}
```

### 实现提醒

并列不替换；输出三科分数，不是只输出总分。
