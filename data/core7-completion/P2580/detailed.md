## P2580 于是他错误的点名开始了

原题：[P2580](https://www.luogu.com.cn/problem/P2580)

### 从问题到算法

同一个名字需要区分三种状态：不在名单、在名单且未点到、在名单且已点到。把名单和已点名记录分开保存，就能让状态转换清楚。

每次收到名字，先查询合法名单。不存在就输出 WRONG，且不修改任何合法同学的记录。存在时向已点名集合插入：插入成功表示此前没有它，输出 OK；插入失败表示早已出现，输出 REPEAT。

重复报错名仍应一直输出 WRONG，不能因为曾经输入过就变成 REPEAT。使用 set 按完整字符串比较，不依赖可能冲突的手写哈希。

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
