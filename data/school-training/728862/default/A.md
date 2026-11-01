## A. Beautiful Year

### 题意

给定年份 $1000\le y\le9000$，找严格大于 $y$ 且四位数字互不相同的最小年份。

### 从零讲：整数拆位与布尔数组

**十进制拆位。** 对非负整数，`value % 10;` 返回个位，`value / 10;` 的整数除法去掉个位。`bool seen[10] = {}` 创建十个初始为假的位置，用数字作为下标。数组有效下标为零到九；访问前由取余保证范围。数组查表和改值均为常数时间。

### 思路

从 $y+1$ 开始逐年枚举。用大小为 $10$ 的布尔数组记录已经出现的数字：重复就跳过该年份；四位数字均不同就输出。

候选年份按递增顺序检查，所以第一个合法年份必然是最小答案。题面保证有解，且 $9012$ 已合法，因此输入范围内最多检查 $8012$ 个候选。每次检查四位，时间 $O(10^4)$，额外空间 $O(1)$。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

bool distinctDigits(int year) {
    bool seen[10] = {};
    while (year > 0) {
        int digit = year % 10;
        if (seen[digit]) return false;
        seen[digit] = true;
        year /= 10;
    }
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int y;
    cin >> y;
    // 从下一年开始，首个合法年份就是最小答案。
    do { ++y; } while (!distinctDigits(y));
    cout << y << '\n';
}
```

### 易错点

必须严格大于输入；数字零也要参与去重。
