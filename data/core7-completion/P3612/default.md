## P3612 Secret Cow Code S

原题：[P3612](https://www.luogu.com.cn/problem/P3612)

### 思路

每轮新串是原串加上“末字符移到最前”的原串。查询在后一半时，第一位对应前一半末位，其余位置向前错一位；反复倒推直到落进初始串。

### 复杂度

时间 O(log N)，空间 O(初始串长度)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    long long p;
    cin >> s >> p;
    long long length = s.size();
    while (length < p)
        length *= 2;
    while (length > (long long)s.size()) {
        long long half = length / 2;
        if (p > half)
            p = p == half + 1 ? half : p - half - 1;
        length = half;
    }
    cout << s[p - 1] << '\n';

    return 0;
}
```

### 实现提醒

后一半第一位单独映射；下标从 1；只增长长度，不生成长串。
