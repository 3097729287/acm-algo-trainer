#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;vector<int>values=a;
sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());
vector<int>tree(values.size()+1);long long answer=0;
for(int j=0;j<n;++j){
    int rank=(int)(lower_bound(values.begin(),values.end(),a[j])-values.begin())+1,count=0;
    for(int p=rank;p>0;p-=p&-p)count+=tree[p];
    answer+=j-count;
    for(int p=rank;p<(int)tree.size();p+=p&-p)++tree[p];
}
cout<<answer<<'\n';
    return 0;
}
