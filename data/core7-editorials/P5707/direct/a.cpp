#include <bits/stdc++.h>
using namespace std;
int main() {
    int s, v;
    cin >> s >> v;
    int walking = (s + v - 1) / v;
    int start = ((8 * 60 - walking - 10) % 1440 + 1440) % 1440;
    cout << setfill('0') << setw(2) << start / 60 << ':' << setw(2) << start % 60 << '\n';
}
