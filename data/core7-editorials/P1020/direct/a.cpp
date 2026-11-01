#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
vector<int>down,tops;int x;while(cin>>x){
    auto a=upper_bound(down.begin(),down.end(),x,greater<int>());if(a==down.end())down.push_back(x);else *a=x;
    auto b=lower_bound(tops.begin(),tops.end(),x);if(b==tops.end())tops.push_back(x);else *b=x;
}cout<<down.size()<<'\n'<<tops.size()<<'\n';
    return 0;
}
