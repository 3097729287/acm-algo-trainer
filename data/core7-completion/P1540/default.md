## P1540 机器翻译

原题：[P1540](https://www.luogu.com.cn/problem/P1540)

### 思路

用集合判断词是否已在内存，用队列记录进入顺序。缺词时查询次数加一；内存满则移走最早进入的词，再加入新词。命中不会调整顺序。

### 复杂度

平均时间 O(n)，空间 O(m)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int m, n;
    cin >> m >> n;
    queue<int> q;
    unordered_set<int> memory;
    int ans = 0;
    while (n--) {
        int x;
        cin >> x;
        if (memory.count(x))
            continue;
        ans++;
        if (!m)
            continue;
        if ((int)q.size() == m) {
            memory.erase(q.front());
            q.pop();
        }
        q.push(x);
        memory.insert(x);
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

命中不移动单词；先淘汰再加入；队列与集合同时更新。
