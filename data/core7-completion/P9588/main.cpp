#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int caseId, q;
    cin >> caseId >> q;
    vector<long long> ends, lengths;
    deque<int> maximum;
    long long total = 0, removed = 0;
    while (q--) {
        int type;
        cin >> type;
        if (type == 1) {
            long long x;
            cin >> x;
            total += x;
            ends.push_back(total);
            lengths.push_back(x);
            int i = ends.size() - 1;
            while (!maximum.empty() && lengths[maximum.back()] <= x)
                maximum.pop_back();
            maximum.push_back(i);
        } else if (type == 2) {
            long long y;
            cin >> y;
            removed += y;
            while (!maximum.empty() && ends[maximum.front()] <= removed)
                maximum.pop_front();
        } else if (type == 3) {
            long long z;
            cin >> z;
            long long p = removed + z;
            int i = lower_bound(ends.begin(), ends.end(), p) - ends.begin();
            cout << p - (ends[i] - lengths[i]) << '\n';
        } else
            cout << lengths[maximum.front()] << '\n';
    }

    return 0;
}
