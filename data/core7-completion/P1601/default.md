## P1601 高精度加法

原题：[P1601](https://www.luogu.com.cn/problem/P1601)

### 思路

从两个数字字符串末尾向前取位，连同进位相加。当前位取模十，新的进位除以十，最后反转结果并去掉多余前导零。

### 复杂度

时间 O(两数位数之和)，空间 O(答案位数)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string a, b;
    cin >> a >> b;
    int i = (int)a.size() - 1, j = (int)b.size() - 1, carry = 0;
    string ans;
    while (i >= 0 || j >= 0 || carry) {
        int sum = carry;
        if (i >= 0)
            sum += a[i--] - '0';
        if (j >= 0)
            sum += b[j--] - '0';
        ans.push_back('0' + sum % 10);
        carry = sum / 10;
    }
    while (ans.size() > 1 && ans.back() == '0')
        ans.pop_back();
    reverse(ans.begin(), ans.end());
    cout << ans << '\n';

    return 0;
}
```

### 实现提醒

最后进位不能漏；数位字符要减 0；至少保留一个零。
