#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string a,b;cin>>a>>b;vector<int>c(a.size()+b.size()+1);
for(int i=0;i<(int)a.size();++i)for(int j=0;j<(int)b.size();++j)
    c[i+j]+=(a[a.size()-1-i]-'0')*(b[b.size()-1-j]-'0');
for(int i=0;i+1<(int)c.size();++i){c[i+1]+=c[i]/10;c[i]%=10;}
while(c.size()>1&&c.back()==0)c.pop_back();
for(int i=(int)c.size()-1;i>=0;--i)cout<<c[i];cout<<'\n';
    return 0;
}
