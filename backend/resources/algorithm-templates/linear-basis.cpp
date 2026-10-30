#include <bits/stdc++.h>
#include <cassert>
using namespace std;

// 无符号 64 位，子集可为空。p[i] 非零时，其最高 1 位恰好为 i。
// 存放的是原数的异或组合，不保证仍是某个原数。
struct XorBasis {
    using U = uint64_t;
    array<U, 64> p{};
    int rank = 0;

    // true：新增独立方向；false：可由已有方向表示，包含输入 0。
    bool insert(U x) {
        for (int i = 63; i >= 0; --i) {
            if (!((x >> i) & 1)) continue;
            if (p[i]) x ^= p[i]; // 消掉最高位，可表示集合保持不变。
            else { p[i] = x; ++rank; return true; }
        }
        return false;
    }
    bool contains(U x) const {
        for (int i = 63; i >= 0; --i)
            if ((x >> i) & 1) x ^= p[i];
        return x == 0;
    }
    // 返回 seed 与任意子集异或后的最大/最小值，默认 seed=0。
    U max_xor(U seed = 0) const {
        for (int i = 63; i >= 0; --i) seed = max(seed, seed ^ p[i]);
        return seed;
    }
    U min_xor(U seed = 0) const {
        for (int i = 63; i >= 0; --i) seed = min(seed, seed ^ p[i]);
        return seed;
    }
    void merge(const XorBasis& other) {
        for (U x : other.p) if (x) insert(x);
    }
    // 不同异或值升序第 k 个，从 0 开始，包含空集产生的 0。
    // rank=64 时全部 uint64_t 下标均合法，不能计算 1ULL<<64。
    optional<U> kth(U k) const {
        if (rank < 64 && k >= (U(1) << rank)) return nullopt;
        auto q = p;
        vector<U> ordered;
        for (int i = 0; i < 64; ++i) if (q[i]) {
            // 清掉其它基向量的主元位，编号的二进制顺序才对应数值顺序。
            for (int j = 0; j < i; ++j)
                if ((q[i] >> j) & 1) q[i] ^= q[j];
            ordered.push_back(q[i]);
        }
        U answer = 0;
        for (int j = 0; j < rank; ++j) if ((k >> j) & 1) answer ^= ordered[j];
        return answer;
    }
    optional<U> min_nonzero() const { return rank ? kth(1) : nullopt; }
};
