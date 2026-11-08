## P6046 纯粹容器

原题：[P6046](https://www.luogu.com.cn/problem/P6046)

### 从问题到算法

把每个存活容器看成它已经击败的连续段的最大值。相邻两者决斗就是删除这两段之间的一条原始分界边，并把两段合并。每轮所有剩余分界等概率被选，因此等价于将 n−1 条原始分界随机排列，依次删除。

位置 i 被淘汰，当且仅当它的连通段首次包含一个更强者。只需考虑左右最近更强者：若要连到更远的强者，途中也必先连到最近的。设左、右距离分别为 L、R，连接到一侧要求该侧路径上的全部分界已经被删除。

经过 t 轮后，一组固定 k 条边全部出现的概率为 C(t,k)/C(n−1,k)。存活概率用左右两个“已经连到强者”事件容斥；两侧路径不重叠，同时发生要求 L+R 条边全部出现。

整数存活轮数 X 的期望为 Σ(t=1..n−1)P(X>=t)。由组合恒等式 Σ(t=k..n−1)C(t,k)=C(n,k+1)，每个长度 k 的路径项求和后等于 n/(k+1)。所以 E=n−1−n/(L+1)−n/(R+1)+n/(L+R+1)，不存在的一侧及其交集项不加入。

最近更大位置用单调栈求出。分数在模 998244353 下用分母逆元表示；全局最大者没有任何更强者，期望正好为 n−1。

### 复杂度

时间 O(n+log MOD)，空间 O(n)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long mod = 998244353;
    vector<int> a(n), left(n, -1), right(n, n), st;
    for (int &x : a)
        cin >> x;
    for (int i = 0; i < n; i++) {
        while (!st.empty() && a[st.back()] < a[i])
            st.pop_back();
        if (!st.empty())
            left[i] = st.back();
        st.push_back(i);
    }
    st.clear();
    for (int i = n - 1; i >= 0; i--) {
        while (!st.empty() && a[st.back()] < a[i])
            st.pop_back();
        if (!st.empty())
            right[i] = st.back();
        st.push_back(i);
    }
    vector<long long> inv(2 * n + 2);
    inv[1] = 1;
    for (int i = 2; i < (int)inv.size(); i++)
        inv[i] = (mod - mod / i) * inv[mod % i] % mod;
    for (int i = 0; i < n; i++) {
        long long ans = n - 1;
        if (left[i] >= 0)
            ans = (ans - n * inv[i - left[i] + 1] % mod + mod) % mod;
        if (right[i] < n)
            ans = (ans - n * inv[right[i] - i + 1] % mod + mod) % mod;
        if (left[i] >= 0 && right[i] < n)
            ans = (ans + n * inv[right[i] - left[i] + 1]) % mod;
        cout << ans << (i + 1 == n ? '\n' : ' ');
    }

    return 0;
}
```

### 实现提醒

存活轮数比被击倒的轮次少一；缺少一侧时去掉对应项；点值互不相同。
