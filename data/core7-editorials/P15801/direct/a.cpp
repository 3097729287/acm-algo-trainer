#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>left(n+1),right(n+1),height(n+1);
for(int u=1;u<=n;++u) cin>>left[u]>>right[u];
vector<int> order={1};
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];if(left[u]) order.push_back(left[u]);if(right[u]) order.push_back(right[u]);}
vector<char> full(n+1),complete(n+1);full[0]=complete[0]=true;int answer=0;
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos],l=left[u],r=right[u];
    height[u]=1+max(height[l],height[r]);
    full[u]=full[l]&&full[r]&&height[l]==height[r];
    complete[u]=(complete[l]&&full[r]&&height[l]==height[r]+1)
              ||(full[l]&&complete[r]&&height[l]==height[r]);
    answer+=complete[u];
}
cout<<answer<<'\n';
    return 0;
}
