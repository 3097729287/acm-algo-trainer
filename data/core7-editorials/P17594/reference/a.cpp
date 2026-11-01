// B. Nailoong and Operations
// 结论：每一步里 y+=p 与 y|=p 只在「当前 y 的第 p 位已经是 1」时不同
//   —— 该位是 0 时两者都把这一位设成 1；该位是 1 时 |= 不动、+= 会进位。
// 于是最终 y = y0 + v，其中 v 是「所有选择 += 的那些 lowbit 之和」，v 必是 x 的子集（按位）。
// 合法性：对每个 x 有、v 没有的二进制位 b，要求 (y0 + (v mod 2^b)) 的第 b 位是 1
//   （因为那一步用的是 |=，得该位本来就被 OR 出来）。
// 按位从低到高做进位 DP：dp[c] = 已定低位的 v 的最小值，c = 进到当前位的进位。
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        long long x, y;
        cin >> x >> y;
        const long long INF = (long long)4e18;
        long long dp[2] = {0, INF};        // 处理到第 0 位前：无进位、代价 0
        for (int p = 0; p <= 30; p++) {
            long long nd[2] = {INF, INF};
            int yb = (int)((y >> p) & 1);
            int xb = (int)((x >> p) & 1);
            for (int c = 0; c < 2; c++) {
                if (dp[c] >= INF) continue;
                if (xb == 0) {                        // v 这一位只能是 0，无约束
                    int c2 = yb & c;
                    nd[c2] = min(nd[c2], dp[c]);
                } else {
                    // v_p = 1：选择 += lowbit，无约束
                    int c2 = yb | c;
                    nd[c2] = min(nd[c2], dp[c] + (1LL << p));
                    // v_p = 0：选择 |=，要求本位结果为 1（yb^c==1），且此后进位必为 0
                    if ((yb ^ c) == 1) nd[0] = min(nd[0], dp[c]);
                }
            }
            dp[0] = nd[0];
            dp[1] = nd[1];
        }
        cout << y + dp[0] << '\n';
    }
    return 0;
}
