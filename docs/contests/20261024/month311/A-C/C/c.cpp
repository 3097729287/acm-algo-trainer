#include <bits/stdc++.h>
using namespace std;
using ull = unsigned long long;
const ull MOD = 998244853;

class FastInput {
    char buffer[1 << 20];
    int at = 0, size = 0;
    char get() {
        if (at == size) { size = fread(buffer, 1, sizeof buffer, stdin); at = 0; }
        return at < size ? buffer[at++] : 0;
    }
public:
    ull read() {
        char c = get();
        while (c && (c < '0' || c > '9')) c = get();
        ull value = 0;
        while (c >= '0' && c <= '9') { value = value * 10 + c - '0'; c = get(); }
        return value;
    }
};

ull power(ull a, ull k) {
    ull result = 1; a %= MOD;
    while (k) {
        if (k & 1) result = result * a % MOD;
        a = a * a % MOD; k >>= 1;
    }
    return result;
}

int main() {
    static FastInput input;
    int t = input.read();
    while (t--) {
        ull n = input.read(), x = input.read(), y = input.read(), z = input.read();
        ull parity = (n & 1) ? y : 0;
        ull variable = y ^ x;
        if ((x & y) != x || (z & y) != z || (z & x) != (parity & x)
            || (n == 1 && (x != y || y != z))
            || (n == 2 && (z & variable) != variable)) {
            puts("-1"); continue;
        }
        // rest 个数还等于 y；改过的数保留最大的三个，防止第二、三名并列。
        ull rest = n, top[3]{}, product = 1;
        int kept = 0;
        auto freeze = [&](ull value) { product = product * (value % MOD) % MOD; };
        auto insert = [&](ull value) {
            if (kept < 3) top[kept++] = value;
            else if (value > top[2]) { freeze(top[2]); top[2] = value; }
            else freeze(value);
            sort(top, top + kept, greater<ull>());
        };
        for (int k = 59; k >= 0; --k) if ((variable >> k) & 1) {
            ull bit = 1ULL << k;
            int count = 1 + (((z >> k) & 1) == (n & 1));
            if (rest >= (ull)count) {
                // 先取尚未改变的 y；这一批一定大于之前改过的数。
                rest -= count;
                for (int j = 0; j < count; ++j) insert(y - bit);
            } else if (rest == 1) {
                // 需要清零两个数：最后一个 y，以及已修改数中的最大者。
                top[0] -= bit;
                sort(top, top + kept, greater<ull>());
                insert(y - bit);
                rest = 0;
            } else {
                for (int j = 0; j < count; ++j) top[j] -= bit;
                sort(top, top + kept, greater<ull>());
            }
        }
        for (int j = 0; j < kept; ++j) freeze(top[j]);
        printf("%llu\n", product * power(y, rest) % MOD);
    }
}
