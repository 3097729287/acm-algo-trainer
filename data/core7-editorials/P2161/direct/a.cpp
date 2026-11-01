#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;set<pair<int,int>>intervals;
while(n--){char op;cin>>op;if(op=='B'){cout<<intervals.size()<<'\n';continue;}int l,r;cin>>l>>r;auto it=intervals.lower_bound({l,INT_MIN});if(it!=intervals.begin()&&prev(it)->second>=l) --it;int removed=0;while(it!=intervals.end()&&it->first<=r){it=intervals.erase(it);++removed;}intervals.insert({l,r});cout<<removed<<'\n';}
    return 0;
}
