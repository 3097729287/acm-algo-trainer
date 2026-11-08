## P1996 约瑟夫问题

原题：[P1996](https://www.luogu.com.cn/problem/P1996)

### 从问题到算法

报数从一开始，所以从当前起点到本轮第 m 人，要前进 m−1 个位置。圈是循环的，取模即可跨过末尾。

删除这个位置后，原来紧接着它的人会左移到同一个数组下标，因此下一轮起点仍使用这个下标；若刚删的是最后一项，下一轮取模会自动回到零。

每轮输出被删除的真实编号，不是数组下标。人数逐次减少直至零，避免最后一次在空数组上取模。

### 复杂度

时间 O(n²)，空间 O(n)，适用于本题的小规模人数。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m;
    cin >> n >> m;
    vector<int> a(n);
    iota(a.begin(), a.end(), 1);
    long long p = 0;
    while (!a.empty()) {
        p = (p + m - 1) % a.size();
        cout << a[p] << (a.size() == 1 ? '\n' : ' ');
        a.erase(a.begin() + p);
    }

    return 0;
}
```

### 实现提醒

报第 m 人要加 m−1；删除后从下一人开始；编号从 1 输出。
