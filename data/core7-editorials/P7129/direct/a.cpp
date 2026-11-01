#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,budget; cin>>n>>budget;
const long long NEG=LLONG_MIN/4;
vector<long long> dp(budget+1,NEG); dp[0]=0; long long answer=0;
for(int stage=0;stage<n;++stage){
    int cost,limit,k,center; cin>>cost>>limit>>k>>center; --center;
    vector<long long> y(k); for(auto &x:y) cin>>x;
    vector<vector<long long>> best(k,vector<long long>(k,NEG));
    best[center][center]=y[center];
    for(int length=1;length<k;++length){
        for(int l=0;l+length<=k;++l){
            int r=l+length-1; if(best[l][r]==NEG) continue;
            if(l>0) best[l-1][r]=max(best[l-1][r],best[l][r]+(length+1)*y[l-1]);
            if(r+1<k) best[l][r+1]=max(best[l][r+1],best[l][r]+(length+1)*y[r+1]);
        }
    }
    long long gain=best[0][k-1];
    vector<long long> next(budget+1,NEG);
    for(int residue=0;residue<cost&&residue<=budget;++residue){
        deque<pair<int,long long>> window;
        for(int q=0,c=residue;c<=budget;++q,c+=cost){
            int j=q-1; // 至少玩一次，前驱不能是当前q。
            if(j>=0&&dp[c-cost]!=NEG){
                long long value=dp[c-cost]-j*gain;
                while(!window.empty()&&window.back().second<=value) window.pop_back();
                window.push_back({j,value});
            }
            while(!window.empty()&&window.front().first<q-limit) window.pop_front();
            if(!window.empty()) next[c]=window.front().second+q*gain;
        }
    }
    dp.swap(next);
    for(long long value:dp) answer=max(answer,value);
}
cout<<answer<<'\n';
    return 0;
}
