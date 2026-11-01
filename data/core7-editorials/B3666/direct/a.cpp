#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<pair<unsigned long long,int>>stack;stack.reserve(n);int answer=0;
for(int i=1;i<=n;++i){unsigned long long x;cin>>x;while(!stack.empty()&&stack.back().first<=x){answer^=stack.back().second;stack.pop_back();}stack.push_back({x,i});answer^=i;cout<<answer<<'\n';}
    return 0;
}
