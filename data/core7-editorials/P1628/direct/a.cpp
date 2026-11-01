#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<string>words(n);for(auto &s:words) cin>>s;string prefix;cin>>prefix;
vector<string>selected;for(const string &s:words) if(s.size()>=prefix.size()&&s.compare(0,prefix.size(),prefix)==0) selected.push_back(s);
sort(selected.begin(),selected.end());for(const string &s:selected) cout<<s<<'\n';
    return 0;
}
