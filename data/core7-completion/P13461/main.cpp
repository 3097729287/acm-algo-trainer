#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    for (int test = 1; test <= tests; test++) {
        long long a, b, minimum;
        cin >> a >> b >> minimum;
        int width = b - a;
        vector<char> composite(width + 1);
        DSU d(width + 1);
        int answer = width + 1;
        for (int p = 2; p <= width; p++)
            if (!composite[p]) {
                for (int j = p + p; j <= width; j += p)
                    composite[j] = 1;
                if (p < minimum)
                    continue;
                long long first = (a + p - 1) / p * p;
                for (long long x = first + p; x <= b; x += p)
                    if (d.join(first - a, x - a))
                        answer--;
            }
        cout << "Case #" << test << ": " << answer << '\n';
    }

    return 0;
}
