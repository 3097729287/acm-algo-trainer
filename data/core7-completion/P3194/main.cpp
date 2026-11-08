#include <bits/stdc++.h>
using namespace std;

struct Line {
    long long k, b;
    int id;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<Line> a(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i].k >> a[i].b;
        a[i].id = i + 1;
    }
    sort(a.begin(), a.end(), [](Line a, Line b) {
        if (a.k != b.k)
            return a.k < b.k;
        return a.b > b.b;
    });
    vector<Line> h;
    vector<long double> start;
    for (auto line : a) {
        if (!h.empty() && line.k == h.back().k)
            continue;
        long double x = -numeric_limits<long double>::infinity();
        while (!h.empty()) {
            x = (long double)(h.back().b - line.b) / (line.k - h.back().k);
            if (x > start.back())
                break;
            h.pop_back();
            start.pop_back();
        }
        if (h.empty())
            x = -numeric_limits<long double>::infinity();
        h.push_back(line);
        start.push_back(x);
    }
    vector<int> ans;
    for (auto line : h)
        ans.push_back(line.id);
    sort(ans.begin(), ans.end());
    for (int id : ans)
        cout << id << ' ';
    cout << '\n';

    return 0;
}
