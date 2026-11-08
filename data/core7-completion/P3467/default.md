## P3467 PLA-Postering

原题：[P3467](https://www.luogu.com.cn/problem/P3467)

### 思路

按横坐标顺序扫描轮廓高度。下降时弹掉更高层，同高度可接续同一建筑；若当前高度为正且高于栈顶，就必须新增一层建筑，计数并压栈。

### 复杂度

时间 O(n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> stack = {0};
    int answer = 0;
    while (n--) {
        int x, h;
        cin >> x >> h;
        while (stack.back() > h)
            stack.pop_back();
        if (stack.back() < h) {
            stack.push_back(h);
            answer++;
        }
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

输入包含横坐标与高度；同高不重复压栈；零高度不计。
