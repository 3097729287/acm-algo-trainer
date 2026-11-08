## P1540 机器翻译

原题：[P1540](https://www.luogu.com.cn/problem/P1540)

### 从问题到算法

题目淘汰的是最早进入内存的单词，不是最近最少使用的单词。命中时既不访问外存，也不改变进入顺序。

队列存实际缓存的单词，队首是最早进入者；集合负责判断当前是否缓存。缺词时计数加一，若队列已满，删除队首在集合中的记录并出队，然后将新词入队、加入集合。两种结构始终保存同一批单词。

容量为零时没有词可以缓存，每个请求都要访问外存，代码也自然单独处理。

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
