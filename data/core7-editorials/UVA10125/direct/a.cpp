#include <bits/stdc++.h>
using namespace std;
struct PairSum{long long value;int first,second;};
bool less_sum(const PairSum&a,const PairSum&b){return a.value<b.value;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;while(cin>>n&&n){vector<long long>a(n);for(auto &x:a)cin>>x;sort(a.begin(),a.end());vector<PairSum>pairs;
    for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)pairs.push_back({a[i]+a[j],i,j});sort(pairs.begin(),pairs.end(),less_sum);
    bool found=false;long long answer=0;
    for(int d=n-1;d>=0&&!found;--d)for(int c=0;c<n&&!found;++c)if(c!=d){
        long long target=a[d]-a[c];auto at=lower_bound(pairs.begin(),pairs.end(),PairSum{target,-1,-1},less_sum);
        // 固定和值下每个下标只出现一次，两个禁用下标最多排除两对。
        for(int inspected=0;at!=pairs.end()&&at->value==target&&inspected<3;++at,++inspected)
            if(at->first!=c&&at->second!=c&&at->first!=d&&at->second!=d){found=true;answer=a[d];break;}
    }
    if(found)cout<<answer<<'\n';else cout<<"no solution\n";
}
    return 0;
}
