#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<int,long long>>previous;long long answer=0;
for(int i=0;i<n;++i){
    int x;cin>>x;vector<pair<int,long long>>current;current.push_back({x,1});
    for(auto group:previous){
        int value=gcd(group.first,x);
        if(current.back().first==value)current.back().second+=group.second;
        else current.push_back({value,group.second});
    }
    for(auto group:current)answer+=1LL*group.first*group.second;
    previous.swap(current);
}
cout<<answer<<'\n';
    return 0;
}
