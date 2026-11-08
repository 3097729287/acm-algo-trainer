## P3929 SAC E#1 - 一道神题 Sequence1

原题：[P3929](https://www.luogu.com.cn/problem/P3929)

### 从问题到算法

固定“低高低高”或“高低高低”后，每对相邻元素的大小方向确定。修改一个位置 p，只会影响 p−1 与 p、p 与 p+1 这两条比较，其它错误无法修复。

找到第一条错误边 (i,i+1)，候选修改点只有 i 或 i+1。对每个候选，若所有错误边都包含这个点，则其余比较原本正确。候选点在该方向中要么是局部峰，要么是局部谷，因此只需把它改得至少和两邻居一样大，或至多一样小，就能同时修复两侧。

因为允许弱不等号，不存在两侧要求互相冲突的情况。没有错误时不用修改；两种方向任意一种可行就输出 Yes。输入包含多组，读至 EOF。

### 复杂度

每组时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    while (cin >> n) {
        vector<long long> a(n);
        for (auto &x : a)
            cin >> x;
        auto ok = [&](bool firstUp) {
            vector<int> bad;
            for (int i = 0; i + 1 < n; i++) {
                bool up = ((i % 2) == 0) == firstUp;
                if (up ? a[i] > a[i + 1] : a[i] < a[i + 1])
                    bad.push_back(i);
            }
            if (bad.empty())
                return true;
            for (int p : {bad[0], bad[0] + 1}) {
                bool valid = true;
                for (int edge : bad)
                    if (edge != p - 1 && edge != p)
                        valid = false;
                if (valid)
                    return true;
            }
            return false;
        };
        cout << (ok(true) || ok(false) ? "Yes" : "No") << '\n';
    }

    return 0;
}
```

### 实现提醒

两种方向都尝试；允许相等；一次修改只能涉及两条相邻边。
