#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int a, b, c, d; cin >> a >> b >> c >> d;
int duration = c * 60 + d - (a * 60 + b);
cout << duration / 60 << ' ' << duration % 60 << '\n';
    return 0;
}
