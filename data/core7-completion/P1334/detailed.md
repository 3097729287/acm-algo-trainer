## P1334 瑞瑞的木板

原题：[P1334](https://www.luogu.com.cn/problem/P1334)

### 从问题到算法

反过来看切割过程，每段最终木板的长度会按它在切割树中的深度被重复计费，总费用是长度乘深度之和。

最优二叉合并树中，可以让两个最短段成为最深的兄弟叶子：若更长段放得更深，交换它与更短段不会增加费用。合并这两个最短段以后，它们可以作为一个新段递归处理，这就是 Huffman 贪心。

小根堆每次直接取最短两段，合并后重新参加后续选择。总费用与合并长度都使用 long long。只有一段时无需切割或合并，费用为零。

### 复杂度

时间 O(n log n)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    priority_queue<long long, vector<long long>, greater<long long>> q;
    while (n--) {
        long long x;
        cin >> x;
        q.push(x);
    }
    long long answer = 0;
    while (q.size() > 1) {
        long long a = q.top();
        q.pop();
        long long b = q.top();
        q.pop();
        answer += a + b;
        q.push(a + b);
    }
    cout << answer << '\n';

    return 0;
}
```

### 实现提醒

每次取当前最短两段；合并结果重新入堆；总费用用 long long。
