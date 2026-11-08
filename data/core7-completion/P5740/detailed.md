## P5740 最厉害的学生

原题：[P5740](https://www.luogu.com.cn/problem/P5740)

### 从问题到算法

题目按总分比较，而输出需要原来的各科分数，因此答案记录应同时保存姓名和三个成绩，不能只存总分。

初始最高分设为小于任何合法总分的值。每读一人，计算总和并严格比较；只有更高才整体更新答案。分数相同不更新，正好满足并列时选输入较早者。

这只需一次扫描，不必排序；排序还容易错误改变并列者的原先次序。

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
