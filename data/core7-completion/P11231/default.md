## P11231 决斗

原题：[P11231](https://www.luogu.com.cn/problem/P11231)

### 思路

一条严格递增链可以按从小到大攻击，最终仅留一个怪兽。同攻击力的怪兽不能在同一条链中，因此最少链数等于某个攻击力的最大出现次数，这就是答案。

### 复杂度

时间 O(n+A)，空间 O(A)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> count(100001);
    int ans = 0;
    while (n--) {
        int x;
        cin >> x;
        ans = max(ans, ++count[x]);
    }
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

攻击必须严格更强才能击败；统计频数最大值即可。
