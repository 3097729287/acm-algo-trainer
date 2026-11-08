#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    for (int &x : a)
        cin >> x;
    vector<int> bottom;
    vector<vector<int>> stacks;
    int washed = 0;
    for (int i = 0; i < n; i++) {
        int x = a[i];
        if (x < washed) {
            cout << i << '\n';
            return 0;
        }
        int p = lower_bound(bottom.begin(), bottom.end(), x) - bottom.begin();
        if (p == (int)bottom.size()) {
            bottom.push_back(x);
            stacks.push_back({});
        }
        while (!stacks[p].empty() && stacks[p].back() < x) {
            washed = max(washed, stacks[p].back());
            stacks[p].pop_back();
        }
        stacks[p].push_back(x);
    }
    cout << n << '\n';

    return 0;
}
