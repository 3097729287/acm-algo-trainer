#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n;
long long cost = 1LL * min(n,150) * 4463;
cost += 1LL * max(0,min(n-150,250)) * 4663;
cost += 1LL * max(0,n-400) * 5663;
// 全部费用精确相加后，只在最后四舍五入一次。
long long tenths = (cost + 500) / 1000;
cout << tenths / 10 << '.' << tenths % 10 << '\n';
    return 0;
}
