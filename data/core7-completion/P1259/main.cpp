#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    string a(n, 'o');
    a += string(n, '*');
    a += "--";
    cout << a << '\n';
    auto move = [&](int from, int to) {
        from--;
        to--;
        swap(a[from], a[to]);
        swap(a[from + 1], a[to + 1]);
        cout << a << '\n';
    };
    function<void(int)> solve = [&](int k) {
        if (k == 4) {
            move(4, 9);
            move(8, 4);
            move(2, 8);
            move(7, 2);
            move(1, 7);
            return;
        }
        move(k, 2 * k + 1);
        move(2 * k - 1, k);
        solve(k - 1);
    };
    solve(n);

    return 0;
}
