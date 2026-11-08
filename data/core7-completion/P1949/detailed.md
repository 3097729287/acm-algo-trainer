## P1949 聪明的打字员

原题：[P1949](https://www.luogu.com.cn/problem/P1949)

### 从问题到算法

密码只有一百万种，光标六种位置，总状态六百万，可以直接使用数组记录距离，避免字符串映射开销。密码虽按整数编码，仍按六位固定十进制权值取出某位，因此前导零不会丢失。

对状态 (code,p)，左右键改变 p；up、down 只在当前位未达九或零时增减相应十进制权值；swap0、swap1 通过两个位置数位差更新整数，光标不动。所有状态转移代价都是一，用普通队列 BFS。

目标只要求密码等于目标串，不限制光标。因此任意光标的目标状态首次出队就能返回。最坏可逐位调整并向右移动，距离不超过几十，使用一个字节保存距离、255 表示未访问即可节省空间。

### 复杂度

时间 O(6·10^6)，空间 O(6·10^6)。

### 参考代码

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s, t;
    cin >> s >> t;
    int start = stoi(s), goal = stoi(t);
    if (start == goal) {
        cout << 0 << '\n';
        return 0;
    }
    int power[6] = {100000, 10000, 1000, 100, 10, 1};
    vector<unsigned char> distance(6000000, 255);
    vector<int> queue;
    queue.reserve(6000000);
    queue.push_back(start * 6);
    distance[start * 6] = 0;
    for (size_t front = 0; front < queue.size(); front++) {
        int state = queue[front], code = state / 6, p = state % 6, depth = distance[state];
        if (code == goal) {
            cout << depth << '\n';
            return 0;
        }
        auto push = [&](int next) {
            if (distance[next] == 255) {
                distance[next] = depth + 1;
                queue.push_back(next);
            }
        };
        if (p)
            push(code * 6 + p - 1);
        if (p < 5)
            push(code * 6 + p + 1);
        int digit = code / power[p] % 10;
        if (digit < 9)
            push((code + power[p]) * 6 + p);
        if (digit > 0)
            push((code - power[p]) * 6 + p);
        for (int q : {0, 5}) {
            int other = code / power[q] % 10;
            int next = code + (other - digit) * power[p] + (digit - other) * power[q];
            push(next * 6 + p);
        }
    }

    return 0;
}
```

### 实现提醒

密码与光标共同编码；up/down 不循环；允许前导零；目标光标任意。
