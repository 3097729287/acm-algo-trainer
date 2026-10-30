#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<long long,long long>>segments(n);for(auto &s:segments)cin>>s.first>>s.second;
sort(segments.begin(),segments.end());long long left=segments[0].first,right=segments[0].second,answer=0;
for(int i=1;i<n;++i){
    if(segments[i].first<=right)right=max(right,segments[i].second);
    else{answer+=right-left;left=segments[i].first;right=segments[i].second;}
}
cout<<answer+right-left<<'\n';
    return 0;
}
