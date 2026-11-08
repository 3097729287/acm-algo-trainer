## CF1267K Key Storage

原题：[CF1267K](https://www.luogu.com.cn/problem/CF1267K)

### 从问题到算法

连续整除可唯一反向还原原数，所以每个满足“第 i 位小于 i+2、最高位非零”的数位序列对应一个密钥。指纹只保留数位多重集合，任务就是给这些数位重新安排位置。

从大数位到小数位放置。若长度为 L，数位 d 可放入容量至少 d 的位置，共 L−max(1,d)+1 个；再减去已经放过的大数位数量，得到当前选择数。乘起来先把相同数位当成不同对象，最后除以每种数位频次的阶乘。上界限制是嵌套的，因此这个乘法直接计完全部安排。

最高位为零会使实际除法提前结束，必须减去。固定最高位零后，去掉一个零，用长度 L−1 的容量重新计算。最后减一排除原密钥。十八位范围的数位不足二十位，中间使用 __int128 保证精确。

### 复杂度

每组 O(L log L)，空间 O(L)，L=O(log k/log log k)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        long long k;
        cin >> k;
        vector<int> d;
        for (int base = 2; k; base++) {
            d.push_back(k % base);
            k /= base;
        }
        auto countWays = [&](vector<int> a) {
            int L = a.size();
            sort(a.rbegin(), a.rend());
            __int128 ways = 1;
            vector<int> cnt(22);
            for (int i = 0; i < L; i++) {
                int choices = L - max(1, a[i]) + 1 - i;
                if (choices <= 0)
                    return (long long)0;
                ways *= choices;
                cnt[a[i]]++;
            }
            for (int c : cnt)
                for (int i = 2; i <= c; i++)
                    ways /= i;
            return (long long)ways;
        };
        long long ans = countWays(d);
        auto it = find(d.begin(), d.end(), 0);
        if (it != d.end()) {
            d.erase(it);
            ans -= countWays(d);
        }
        cout << ans - 1 << '\n';
    }

    return 0;
}
```

### 实现提醒

最高位不能为零；相同余数要除重；最后减去原数。
