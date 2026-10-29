#include <bits/stdc++.h>
using namespace std;
int sticks(int x){int use[10]={6,2,5,5,4,5,6,3,7,6},answer=0;do{answer+=use[x%10];x/=10;}while(x);return answer;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>cost(19999);for(int x=0;x<19999;++x)cost[x]=sticks(x);
vector<int>candidate;for(int x=0;x<10000;++x)if(cost[x]<=n-8)candidate.push_back(x);
int answer=0;for(int a:candidate)for(int b:candidate)if(cost[a]+cost[b]+cost[a+b]+4==n)++answer;
cout<<answer<<'\n';
    return 0;
}
