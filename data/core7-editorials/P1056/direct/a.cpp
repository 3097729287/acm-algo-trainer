#include <bits/stdc++.h>
using namespace std;
void print_best(const vector<int>&counts,int number){
    vector<pair<int,int>>rank;for(int i=1;i<(int)counts.size();++i)rank.push_back({counts[i],i});
    sort(rank.rbegin(),rank.rend());vector<int>answer;for(int i=0;i<number;++i)answer.push_back(rank[i].second);
    sort(answer.begin(),answer.end());for(int i=0;i<number;++i){if(i)cout<<' ';cout<<answer[i];}cout<<'\n';
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int m,n,k,l,d;cin>>m>>n>>k>>l>>d;vector<int>rows(m),columns(n);
while(d--){int x,y,p,q;cin>>x>>y>>p>>q;if(x!=p)++rows[min(x,p)];else ++columns[min(y,q)];}
print_best(rows,k);print_best(columns,l);
    return 0;
}
