#include <bits/stdc++.h>
#include <cassert>
using namespace std;

// 离散 Li Chao 树：先给出所有可能查询的横坐标，再插入整条直线，求最小值。
// 用 __int128 计算 k*x+b；不使用可能与合法答案冲突的 INF 哨兵。
struct LiChao {
    using Wide = __int128_t;
    struct Line {
        long long k, b;
        Wide at(long long x) const { return Wide(k) * x + b; }
    };
    vector<long long> xs;
    vector<optional<Line>> tree;
    explicit LiChao(vector<long long> coordinates) : xs(move(coordinates)) {
        sort(xs.begin(), xs.end()); xs.erase(unique(xs.begin(), xs.end()), xs.end());
        tree.resize(4 * max<size_t>(1, xs.size()));
    }
    void add(Line line) { if (!xs.empty()) add(line,1,0,(int)xs.size()-1); }
    void add(Line line, int p, int l, int r) {
        if (!tree[p]) { tree[p] = line; return; }
        int m = l + (r-l)/2;
        bool left = line.at(xs[l]) < tree[p]->at(xs[l]);
        bool middle = line.at(xs[m]) < tree[p]->at(xs[m]);
        if (middle) swap(line, *tree[p]); // 当前结点保留在中点更小的线。
        if (l == r) return;
        // 两条直线至多交一次，落败线只可能在一侧重新胜出。
        if (left != middle) add(line,p*2,l,m);
        else add(line,p*2+1,m+1,r);
    }
    optional<Wide> query(long long x) const {
        auto it = lower_bound(xs.begin(), xs.end(), x);
        if (it == xs.end() || *it != x) return nullopt; // 未登记的坐标不外推。
        int target = it-xs.begin(), p=1, l=0, r=(int)xs.size()-1;
        optional<Wide> answer;
        while (true) {
            if (tree[p]) {
                Wide value = tree[p]->at(x);
                if (!answer || value < *answer) answer = value;
            }
            if (l == r) return answer;
            int m=l+(r-l)/2;
            if (target <= m) { p*=2; r=m; } else { p=p*2+1; l=m+1; }
        }
    }
};
