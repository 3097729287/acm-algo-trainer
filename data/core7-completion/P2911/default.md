## P2911 Bovine Bones G

原题：[P2911](https://www.luogu.com.cn/problem/P2911)

### 思路

逐个枚举三个骰子的所有点数组合，累计和的出现次数，再从小到大找出现次数最多的和。

### 复杂度

时间 O(s1·s2·s3)，空间 O(s1+s2+s3)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int a, b, c;
    cin >> a >> b >> c;
    vector<int> cnt(a + b + c + 1);
    for (int x = 1; x <= a; x++)
        for (int y = 1; y <= b; y++)
            for (int z = 1; z <= c; z++)
                cnt[x + y + z]++;
    int ans = 0;
    for (int i = 1; i < (int)cnt.size(); i++)
        if (cnt[i] > cnt[ans])
            ans = i;
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

点数从 1 开始；并列时选择最小和。
