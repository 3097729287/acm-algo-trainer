#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<long long>>a(n,vector<long long>(n));for(auto &row:a)for(auto &x:row)cin>>x;
long long answer=LLONG_MIN;
for(int top=0;top<n;++top){vector<long long>sum(n);
    for(int bottom=top;bottom<n;++bottom){
        for(int column=0;column<n;++column)sum[column]+=a[bottom][column];
        long long ending=sum[0];answer=max(answer,ending);
        for(int column=1;column<n;++column){ending=max(sum[column],ending+sum[column]);answer=max(answer,ending);}
    }
}
cout<<answer<<'\n';
    return 0;
}
