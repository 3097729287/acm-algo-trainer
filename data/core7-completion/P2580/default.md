## P2580 于是他错误的点名开始了

原题：[P2580](https://www.luogu.com.cn/problem/P2580)

### 思路

用集合保存合法姓名，另一个集合保存已经正确点到的姓名。先判断是否合法，再区分首次点名和重复点名。

### 复杂度

时间 O((n+m)·L log(n+m))，空间 O((n+m)L)，L 为姓名长度。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    set<string> names, called;
    while (n--) {
        string s;
        cin >> s;
        names.insert(s);
    }
    int m;
    cin >> m;
    while (m--) {
        string s;
        cin >> s;
        if (!names.count(s))
            cout << "WRONG\n";
        else
            cout << (called.insert(s).second ? "OK" : "REPEAT") << '\n';
    }

    return 0;
}
```

### 实现提醒

先判断名单合法性；错误名字不能进入正确点名记录。
