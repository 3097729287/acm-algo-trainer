#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t; cin >> t;
const double pi = 3.141593;
switch (t) {
case 1: cout << "I love Luogu!\n"; break;
case 2: cout << 2+4 << ' ' << 10-2-4 << '\n'; break;
case 3: cout << 14/4 << '\n' << 14/4*4 << '\n' << 14%4 << '\n'; break;
case 4: cout << setprecision(6) << 500.0/3 << '\n'; break;
case 5: cout << (260+220)/(12+20) << '\n'; break;
case 6: cout << sqrt(9*9+6*6) << '\n'; break;
case 7: cout << "110\n90\n0\n"; break;
case 8: cout << 2*pi*5 << '\n' << pi*25 << '\n' << 4.0/3*pi*125 << '\n'; break;
case 9: { int x=1; for(int i=0;i<3;++i) x=(x+1)*2; cout << x << '\n'; break; }
case 10: cout << 9 << '\n'; break;
case 11: cout << 100.0/(8-5) << '\n'; break;
case 12: cout << 'M'-'A'+1 << '\n' << char('A'+17) << '\n'; break;
case 13: cout << (int)cbrt(4.0/3*pi*(4*4*4+10*10*10)) << '\n'; break;
case 14: cout << 50 << '\n'; break;
}
    return 0;
}
