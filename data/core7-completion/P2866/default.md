## P2866 Bad Hair Day S

原题：[P2866](https://www.luogu.com.cn/problem/P2866)

### 思路

从左往右扫描，身高不大于当前牛的栈顶都被当前牛挡住，弹出。剩余栈中每头牛都能看见当前牛，答案加栈大小，再压入当前身高。

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
    vector<long long> stack;
    long long answer = 0;
    while (n--) {
        long long x;
        cin >> x;
        while (!stack.empty() && stack.back() <= x)
            stack.pop_back();
        answer += stack.size();
        stack.push_back(x);
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

同身高也会挡住，应弹出小于等于；先弹再计数；答案六十四位。
