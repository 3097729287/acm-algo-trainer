#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,queries; cin>>n>>queries;
vector<int> a(n+1); for(int i=1;i<=n;++i) cin>>a[i];
const int SHIFT=1000000; vector<int> frequency(2*SHIFT+1);
int stride=n+2; vector<long long> answer(1LL*stride*stride);
auto at=[&](int l,int r)->long long& {return answer[1LL*l*stride+r];};
for(int l=n;l>=1;--l){
    for(int r=l+1;r<=n;++r){
        int needed=-a[l]-a[r];
        long long endpoints=(needed>=-SHIFT&&needed<=SHIFT)?frequency[needed+SHIFT]:0;
        at(l,r)=at(l+1,r)+at(l,r-1)-at(l+1,r-1)+endpoints;
        ++frequency[a[r]+SHIFT]; // 先查询，再让右端成为下一轮的中间项。
    }
    for(int r=l+1;r<=n;++r) --frequency[a[r]+SHIFT];
}
while(queries--){int l,r;cin>>l>>r;cout<<at(l,r)<<'\n';}
    return 0;
}
