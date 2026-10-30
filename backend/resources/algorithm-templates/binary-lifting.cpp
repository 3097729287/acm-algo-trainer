#include <bits/stdc++.h>
#include <cassert>
using namespace std;

// next[v] 是 [0,n) 中的后继。允许自环和一般函数图，不要求是一棵树。
struct BinaryLifting {
    vector<array<int, 64>> up;
    explicit BinaryLifting(const vector<int>& next) : up(next.size()) {
        for (int v = 0; v < (int)next.size(); ++v) {
            assert(0 <= next[v] && next[v] < (int)next.size());
            up[v][0] = next[v];
        }
        // 两段 2^(j-1) 步拼成 2^j 步，必须先算完整的上一列。
        for (int j = 1; j < 64; ++j)
            for (int v = 0; v < (int)next.size(); ++v)
                up[v][j] = up[up[v][j-1]][j-1];
    }
    int jump(int v, uint64_t steps) const {
        assert(0 <= v && v < (int)up.size());
        for (int j = 0; j < 64; ++j) if ((steps >> j) & 1) v = up[v][j];
        return v;
    }
};
