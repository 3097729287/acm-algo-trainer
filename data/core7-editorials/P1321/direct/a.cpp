#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s; cin >> s; int boys=0, girls=0, n=s.size();
for(int i=0;i+2<n;++i) boys += s[i]=='b'||s[i+1]=='o'||s[i+2]=='y';
for(int i=0;i+3<n;++i) girls += s[i]=='g'||s[i+1]=='i'||s[i+2]=='r'||s[i+3]=='l';
cout << boys << '\n' << girls << '\n';
    return 0;
}
