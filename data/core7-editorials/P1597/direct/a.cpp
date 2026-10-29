#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s; cin >> s; int value[3]={};
for(int i=0;i<(int)s.size();i+=5) {
    char rhs=s[i+3];
    int x=isdigit((unsigned char)rhs)?rhs-'0':value[rhs-'a'];
    value[s[i]-'a']=x;
}
cout << value[0] << ' ' << value[1] << ' ' << value[2] << '\n';
    return 0;
}
