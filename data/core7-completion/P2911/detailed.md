## P2911 Bovine Bones G

原题：[P2911](https://www.luogu.com.cn/problem/P2911)

### 从问题到算法

三个骰子的每一面等概率，任意点数组合的概率相同，所以和的概率与产生这个和的组合数成正比。

开一个长度为三个最大点数之和加一的频数数组。三层循环枚举 x、y、z，把 freq[x+y+z] 加一。然后按和递增扫描，仅在频数严格更大时更新答案。这样出现次数相同时，自动保留较小的和。

没有必要使用浮点概率，也不能仅凭骰子平均值四舍五入，因为多个和可能并列最高。

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
