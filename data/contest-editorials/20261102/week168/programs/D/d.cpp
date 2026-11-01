#include <bits/stdc++.h>
using namespace std;
vector<int> parent_link;
int find_next(int x) {
    int root = x;
    while (parent_link[root] != root) root = parent_link[root];
    // 路径压缩：以后直接跳到当前第一个可用位置。
    while (x != root) { int next = parent_link[x]; parent_link[x] = root; x = next; }
    return root;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; ++i) cin >> a[i];
    parent_link.resize(n + 2);
    iota(parent_link.begin(), parent_link.end(), 0);
    int pos = 1;
    long long answer = 0;
    for (int turn = 0; turn < m; ++turn) {
        long long d;
        cin >> d;
        // d 按原来的 n 个格子计算，不能只在空格中数步数。
        int start = 1 + (pos - 1 + d) % n;
        pos = find_next(start);
        if (pos == n + 1) pos = find_next(1);
        answer += a[pos];
        parent_link[pos] = find_next(pos + 1);
    }
    cout << answer << ' ' << pos << '\n';
}
