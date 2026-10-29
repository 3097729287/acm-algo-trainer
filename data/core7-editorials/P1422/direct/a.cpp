#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n;
double cost = min(n,150) * 0.4463;
cost += max(0,min(n-150,250)) * 0.4663;
cost += max(0,n-400) * 0.5663;
cout << fixed << setprecision(1) << cost << '\n';
    return 0;
}
