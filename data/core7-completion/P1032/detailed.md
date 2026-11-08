## P1032 字串变换（疑似错题）

原题：[P1032](https://www.luogu.com.cn/problem/P1032)

### 从问题到算法

一次操作只能替换某个具体出现位置的子串，所以同一条规则在一个字符串中可能产生多个后继，必须枚举全部出现位置，包括相互重叠的位置。BFS 首次访问某串的层数就是最少替换次数。

十层单向搜索分支可能太多，改为两边各搜五层。反向搜索把每条规则的左右串交换；如果存在长度 L<=10 的路径，可在距离起点 min(5,L) 的位置切开，剩余长度也不超过五，所以两个搜索集合必有交集。

每边用映射保存最短距离并去重，深度五的状态保留但不继续扩展。最后枚举交集，取距离和最小者；超过十步或没有交集时输出 NO ANSWER!。

### 复杂度

时间与五层内实际产生的不同字符串及匹配位置数量成正比，空间与访问状态总长度成正比。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string start, goal;
    cin >> start >> goal;
    vector<pair<string, string>> rules;
    string a, b;
    while (cin >> a >> b)
        rules.push_back({a, b});
    auto search = [&](string initial, bool reverseRule) {
        unordered_map<string, int> distance;
        queue<string> q;
        distance[initial] = 0;
        q.push(initial);
        while (!q.empty()) {
            string s = q.front();
            q.pop();
            int depth = distance[s];
            if (depth == 5)
                continue;
            for (auto rule : rules) {
                string from = reverseRule ? rule.second : rule.first,
                       to = reverseRule ? rule.first : rule.second;
                for (size_t pos = s.find(from); pos != string::npos; pos = s.find(from, pos + 1)) {
                    string next = s.substr(0, pos) + to + s.substr(pos + from.size());
                    if (distance.emplace(next, depth + 1).second)
                        q.push(next);
                }
            }
        }
        return distance;
    };
    auto forward = search(start, false), backward = search(goal, true);
    int ans = 11;
    for (auto &[s, d] : forward) {
        auto it = backward.find(s);
        if (it != backward.end())
            ans = min(ans, d + it->second);
    }
    if (ans <= 10)
        cout << ans << '\n';
    else
        cout << "NO ANSWER!\n";

    return 0;
}
```

### 实现提醒

枚举同规则所有出现位置；反向规则要交换两端；恰好十步也允许。
