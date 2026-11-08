## SP4033 PHONELST - Phone List

原题：[SP4033](https://www.luogu.com.cn/problem/SP4033)

### 从问题到算法

字典序会把拥有同一前缀的字符串放在连续的一段中，而且前缀本身排在它所有更长的扩展之前。因此只要某号码是另一个号码的前缀，排序后它紧邻的后一个号码也必定拥有这个前缀。

依次比较相邻号码，检查后一项开头与前一项是否相同。找到一次就不一致；全部检查通过才一致。相同的两个号码也互为前缀，应判为不一致。

号码须作为字符串读取，不能转整数，否则前导零会丢失，长度与前缀关系会改变。

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
