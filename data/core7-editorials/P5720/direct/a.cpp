#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int a; cin >> a;
int day = 1;
while (a > 1) { a /= 2; ++day; }
cout << day << '\n';
    return 0;
}
