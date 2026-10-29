#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int a, b, c, d; cin >> a >> b >> c >> d;
int hours = c - a, minutes = d - b;
while (minutes < 0) { --hours; minutes += 60; }
while (minutes >= 60) { ++hours; minutes -= 60; }
cout << hours << ' ' << minutes << '\n';
    return 0;
}
