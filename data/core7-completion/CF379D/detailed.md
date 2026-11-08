## CF379D New Year Letter

原题：[CF379D](https://www.luogu.com.cn/problem/CF379D)

### 从问题到算法

拼接 X+Y 的新增匹配只有边界：当 X 末尾 A、Y 开头 C 时加一。其它内部匹配保持不变，所以长度再大也只需保存首尾与计数。

对给定初始长度，用字母 A、B、C 动态生成可行的 (首,尾,数量) 状态，并保留一条构造串。其它大写字母都可换成 B，因为它们既不形成 AC，也不会改变 A、C 的边界作用。

枚举两个可行描述，按题目 s_i=s_(i−2)+s_(i−1) 推出第 k 项，计数超过目标可截断为 x+1，防止增长溢出。首尾与计数相同的字符串对后续完全等价，所以只保留一条代表不会漏解。命中就输出两条原始串，否则输出指定问候语。

### 复杂度

设候选描述数 O(n+m)，时间 O(n²+m²+nm·k)，空间 O(n²+m²) 用于保存代表串。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;
struct Descriptor {
    string word;
    char first, last;
    long long count;
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int k;
    long long x;
    int n, m;
    cin >> k >> x >> n >> m;
    auto generate = [&](int length) {
        vector<Descriptor> result;
        for (char first : string("ABC")) {
            vector<vector<string>> dp(3, vector<string>(length + 1));
            dp[first - 'A'][0] = string(1, first);
            for (int used = 1; used < length; used++) {
                vector<vector<string>> next(3, vector<string>(length + 1));
                for (int last = 0; last < 3; last++)
                    for (int count = 0; count <= length; count++)
                        if (!dp[last][count].empty())
                            for (int c = 0; c < 3; c++) {
                                int nc = count + (last == 0 && c == 2);
                                if (nc <= length && next[c][nc].empty())
                                    next[c][nc] = dp[last][count] + char('A' + c);
                            }
                dp.swap(next);
            }
            for (int last = 0; last < 3; last++)
                for (int count = 0; count <= length; count++)
                    if (!dp[last][count].empty())
                        result.push_back({dp[last][count], first, char('A' + last), count});
        }
        return result;
    };
    auto left = generate(n), right = generate(m);
    for (auto A : left)
        for (auto B : right) {
            long long a = A.count, b = B.count;
            char fa = A.first, la = A.last, fb = B.first, lb = B.last;
            for (int step = 3; step <= k; step++) {
                long long next = min(x + 1, a + b + (la == 'A' && fb == 'C'));
                char nf = fa, nl = lb;
                a = b;
                b = next;
                fa = fb;
                la = lb;
                fb = nf;
                lb = nl;
            }
            if (b == x) {
                cout << A.word << '\n' << B.word << '\n';
                return 0;
            }
        }
    cout << "Happy new year!\n";

    return 0;
}
```

### 实现提醒

拼接顺序是前二项加前一项；只统计 AC；同一描述任取代表串。
