#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;string best;int winner=0;
for(int i=1;i<=n;++i){string votes;cin>>votes;
    size_t p=votes.find_first_not_of('0');votes=p==string::npos?"0":votes.substr(p);
    if(votes.size()>best.size()||(votes.size()==best.size()&&votes>best)){best=votes;winner=i;}
}
cout<<winner<<'\n'<<best<<'\n';
    return 0;
}
