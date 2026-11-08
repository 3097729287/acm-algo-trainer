#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    const int V = 131071;
    vector<int> assign(4 * V, 0);
    vector<char> flip(4 * V);
    auto apply = [&](int v, int type) {
        if (type < 2) {
            assign[v] = type;
            flip[v] = 0;
        } else if (assign[v] >= 0)
            assign[v] ^= 1;
        else
            flip[v] ^= 1;
    };
    function<void(int)> push = [&](int v) {
        if (assign[v] >= 0) {
            apply(v * 2, assign[v]);
            apply(v * 2 + 1, assign[v]);
            assign[v] = -1;
        }
        if (flip[v]) {
            apply(v * 2, 2);
            apply(v * 2 + 1, 2);
            flip[v] = 0;
        }
    };
    function<void(int, int, int, int, int, int)> update = [&](int v, int l, int r, int L, int R,
                                                              int type) {
        if (L > R)
            return;
        if (L <= l && r <= R) {
            apply(v, type);
            return;
        }
        push(v);
        int mid = (l + r) / 2;
        if (L <= mid)
            update(v * 2, l, mid, L, R, type);
        if (R > mid)
            update(v * 2 + 1, mid + 1, r, L, R, type);
    };
    char op, left, right, comma;
    int a, b;
    while (cin >> op >> left >> a >> comma >> b >> right) {
        int L = 2 * a + (left == '('), R = 2 * b - (right == ')');
        if (L > R) {
            if (op == 'I' || op == 'C')
                apply(1, 0);
            continue;
        }
        if (op == 'I' || op == 'C') {
            update(1, 0, V - 1, 0, L - 1, 0);
            update(1, 0, V - 1, R + 1, V - 1, 0);
        }
        if (op == 'U')
            update(1, 0, V - 1, L, R, 1);
        if (op == 'D')
            update(1, 0, V - 1, L, R, 0);
        if (op == 'S' || op == 'C')
            update(1, 0, V - 1, L, R, 2);
    }
    vector<char> chosen(V);
    function<void(int, int, int)> collect = [&](int v, int l, int r) {
        if (assign[v] >= 0) {
            fill(chosen.begin() + l, chosen.begin() + r + 1, assign[v]);
            return;
        }
        push(v);
        int mid = (l + r) / 2;
        collect(v * 2, l, mid);
        collect(v * 2 + 1, mid + 1, r);
    };
    collect(1, 0, V - 1);
    bool any = false;
    for (int l = 0; l < V;) {
        if (!chosen[l]) {
            l++;
            continue;
        }
        int r = l;
        while (r + 1 < V && chosen[r + 1])
            r++;
        if (any)
            cout << ' ';
        any = true;
        cout << (l % 2 ? '(' : '[') << l / 2 << ',' << (r + 1) / 2 << (r % 2 ? ')' : ']');
        l = r + 1;
    }
    if (!any)
        cout << "empty set";
    cout << '\n';

    return 0;
}
