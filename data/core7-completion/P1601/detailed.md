## P1601 高精度加法

原题：[P1601](https://www.luogu.com.cn/problem/P1601)

### 从问题到算法

整数类型无法保存很长的十进制数，但竖式加法每次只需要当前两个数位和一个进位，数值最大十九。

用两个下标从字符串末尾开始。某个数已用完时当作该位为零；只要还有任何一位或进位，就继续处理。将这一位和的个位字符追加到答案，十位作为下一轮进位。

生成顺序是低位到高位，最后整体反转。输入允许前导零时，反转前删去答案高位的多余零，但至少保留一位，使零正确输出为 0。

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
