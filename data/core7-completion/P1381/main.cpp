#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    unordered_map<string, int> dict;
    while (n--) {
        string s;
        cin >> s;
        if (!dict.count(s)) {
            int id = dict.size();
            dict[s] = id;
        }
    }
    int m;
    cin >> m;
    vector<int> a(m, -1), exists(dict.size());
    for (int i = 0; i < m; i++) {
        string s;
        cin >> s;
        auto it = dict.find(s);
        if (it != dict.end()) {
            a[i] = it->second;
            exists[it->second] = 1;
        }
    }
    int need = accumulate(exists.begin(), exists.end(), 0);
    cout << need << '\n';
    if (!need) {
        cout << 0 << '\n';
        return 0;
    }
    vector<int> freq(dict.size());
    int have = 0, l = 0, best = m + 1;
    for (int r = 0; r < m; r++) {
        if (a[r] >= 0 && freq[a[r]]++ == 0)
            have++;
        while (have == need) {
            best = min(best, r - l + 1);
            if (a[l] >= 0 && --freq[a[l]] == 0)
                have--;
            l++;
        }
    }
    cout << best << '\n';

    return 0;
}
