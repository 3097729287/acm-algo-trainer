## P2866 Bad Hair Day S

原题：[P2866](https://www.luogu.com.cn/problem/P2866)

### 从问题到算法

某头牛向右看，遇到第一头不比自己矮的牛就被挡住。扫描到当前身高 h 时，栈里不高于 h 的牛从此再也看不到更右侧，且它们不能把当前牛算作可见的更矮牛，所以先全部弹出。

剩余牛的身高严格递减且都大于 h，中间没有能挡住它们的牛，因此每头都新增一次可见关系，贡献就是栈大小。然后当前牛入栈，等待更矮者出现。

每头牛最多进出栈一次，所以总时间线性；可见对数最多平方级，答案用 long long。

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
