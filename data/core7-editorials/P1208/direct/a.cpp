#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long need;int m;cin>>need>>m;vector<pair<int,int>>farm(m);for(auto &f:farm)cin>>f.first>>f.second;
sort(farm.begin(),farm.end());long long answer=0;
for(auto f:farm){long long take=min(need,(long long)f.second);answer+=take*f.first;need-=take;if(need==0)break;}
cout<<answer<<'\n';
    return 0;
}
