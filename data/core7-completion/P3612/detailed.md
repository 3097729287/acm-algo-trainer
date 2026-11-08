## P3612 Secret Cow Code S

原题：[P3612](https://www.luogu.com.cn/problem/P3612)

### 从问题到算法

字符串长度每轮翻倍，目标下标可到十的十八次方，实际生成字符串不可行。但每个新位置都对应上一轮的一个位置。

设上一轮长度为 half。前 half 个字符不变；后一半的第一个字符来自上一轮最后一位，所以下标 half+1 映射为 half；后一半其它位置 p 映射为 p−half−1。

先把长度翻倍到足够覆盖查询，再每次折半并进行上述映射。位置始终保持从一开始，最后落进原串后输出它的第 p−1 个字符。

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
