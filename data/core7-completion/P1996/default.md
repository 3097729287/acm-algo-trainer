## P1996 约瑟夫问题

原题：[P1996](https://www.luogu.com.cn/problem/P1996)

### 思路

保存仍在圈中的编号，当前报数起点为位置 p。本轮删除位置 (p+m−1)%人数，删除后该位置自动指向下一位报数者，依次输出。

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
