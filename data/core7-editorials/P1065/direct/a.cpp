#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int m,n;cin>>m>>n;int q=m*n;vector<int>order(q);for(int &x:order){cin>>x;--x;}
vector<vector<int>>machine(n,vector<int>(m)),duration=machine;
for(auto &row:machine)for(int &x:row){cin>>x;--x;}
for(auto &row:duration)for(int &x:row)cin>>x;
vector<int>next(n),finish(n);vector<vector<pair<int,int>>>busy(m);int answer=0;
for(int job:order){int op=next[job]++,which=machine[job][op],d=duration[job][op],start=finish[job];
    auto &slots=busy[which];int pos=0;
    while(pos<(int)slots.size()){
        if(start+d<=slots[pos].first)break;
        start=max(start,slots[pos].second);++pos;
    }
    slots.insert(slots.begin()+pos,{start,start+d});finish[job]=start+d;answer=max(answer,finish[job]);
}cout<<answer<<'\n';
    return 0;
}
