## SP4033 PHONELST - Phone List

原题：[SP4033](https://www.luogu.com.cn/problem/SP4033)

### 思路

将所有电话号码按字典序排序。若一个号码是另一个的前缀，它们之间紧邻它的下一个号码也以它为前缀，因此只需检查相邻两项。

### 复杂度

时间 O(nL log n)，空间 O(nL)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<string> a(n);
        for (auto &s : a)
            cin >> s;
        sort(a.begin(), a.end());
        bool ok = true;
        for (int i = 1; i < n; i++)
            if (a[i].compare(0, a[i - 1].size(), a[i - 1]) == 0)
                ok = false;
        cout << (ok ? "YES" : "NO") << '\n';
    }

    return 0;
}
```

### 实现提醒

使用字符串保存前导零；重复号码也不一致；每组读完再判断。
