#include <bits/stdc++.h>
using namespace std;
map<vector<int>,int> memo;
int solve(vector<int> a){if(a.size()==1)return a[0];if(memo.count(a))return memo[a];int best=-1;
for(int i=0;i<(int)a.size();++i){for(int left=1;left<a[i];++left){vector<int>b=a;if(i>0)b[i-1]+=left;if(i+1<(int)a.size())b[i+1]+=a[i]-left;b.erase(b.begin()+i);best=max(best,solve(b));}}
return memo[a]=best;}
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<int>a(n);for(int &v:a)cin>>v;memo.clear();cout<<solve(a)<<'\n';}}
