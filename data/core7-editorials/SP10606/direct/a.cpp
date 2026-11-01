#include <bits/stdc++.h>
using namespace std;
const int STATES=59049;
int transition[STATES][10];bool valid[STATES];unsigned long long memo[21][STATES];
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
array<int,10>power3;power3[0]=1;for(int d=1;d<10;++d) power3[d]=power3[d-1]*3;
for(int state=0;state<STATES;++state){
    valid[state]=state!=0;
    for(int d=0;d<10;++d){
        int count=state/power3[d]%3;
        if((d%2==0&&count==2)||(d%2==1&&count==1)) valid[state]=false;
        int next=count==1?2:1;transition[state][d]=state+(next-count)*power3[d];
    }
}
transition[0][0]=0;memset(memo,255,sizeof(memo));
auto prefix=[&](unsigned long long x){
    string digits=to_string(x);
    function<unsigned long long(int,int,bool)> dfs=[&](int pos,int state,bool tight)->unsigned long long{
        if(pos==int(digits.size())) return valid[state];int remaining=digits.size()-pos;
        auto &saved=memo[remaining][state];if(!tight&&saved!=ULLONG_MAX) return saved;
        unsigned long long answer=0;int limit=tight?digits[pos]-'0':9;
        for(int d=0;d<=limit;++d) answer+=dfs(pos+1,transition[state][d],tight&&d==limit);
        if(!tight) saved=answer;return answer;
    };
    return dfs(0,0,true);
};
int t;cin>>t;while(t--){unsigned long long a,b;cin>>a>>b;cout<<prefix(b)-prefix(a-1)<<'\n';}
    return 0;
}
