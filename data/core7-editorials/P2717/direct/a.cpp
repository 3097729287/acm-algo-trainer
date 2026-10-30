#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;long long k;cin>>n>>k;vector<long long>prefix(n+1);
for(int i=1;i<=n;++i){long long x;cin>>x;prefix[i]=prefix[i-1]+x-k;}
vector<long long>values=prefix;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());
vector<int>tree(values.size()+1);long long answer=0;
for(long long sum:prefix){
    int rank=(int)(lower_bound(values.begin(),values.end(),sum)-values.begin())+1;
    for(int p=rank;p>0;p-=p&-p)answer+=tree[p]; // 查询包含与当前相等的前缀
    for(int p=rank;p<(int)tree.size();p+=p&-p)++tree[p];
}
cout<<answer<<'\n';
    return 0;
}
