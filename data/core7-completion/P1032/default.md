## P1032 字串变换（疑似错题）

原题：[P1032](https://www.luogu.com.cn/problem/P1032)

### 思路

从起始串按原规则搜索至五步，从目标串按反向规则搜索至五步。任意不超过十步的最短路径都能在两边覆盖的某个中间串相遇，取两侧距离和的最小值。

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
