## P3929 SAC E#1 - 一道神题 Sequence1

原题：[P3929](https://www.luogu.com.cn/problem/P3929)

### 思路

分别尝试两种波动方向，记录不满足的相邻比较。若有错误，唯一修改位置必须是第一条错误边的某个端点；检查所有错误是否都与它相邻即可。

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
