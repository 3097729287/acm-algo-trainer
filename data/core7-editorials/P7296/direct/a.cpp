#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string text;cin>>text;vector<int>index(26,-1);int n=0;
for(char c:text) if(index[c-'a']<0) index[c-'a']=n++;
vector<vector<int>>count(n,vector<int>(n));
for(size_t i=1;i<text.size();++i) ++count[index[text[i-1]-'a']][index[text[i]-'a']];
int half=n/2,leftStates=1<<half,rightStates=1<<(n-half);
vector<vector<int>>left(n,vector<int>(leftStates)),right(n,vector<int>(rightStates));
for(int row=0;row<n;++row){
    for(int mask=1;mask<leftStates;++mask){int bit=0;while(!(mask>>bit&1)) ++bit;left[row][mask]=left[row][mask^(1<<bit)]+count[row][bit];}
    for(int mask=1;mask<rightStates;++mask){int bit=0;while(!(mask>>bit&1)) ++bit;right[row][mask]=right[row][mask^(1<<bit)]+count[row][half+bit];}
}
int states=1<<n;vector<int>dp(states,text.size()+1);dp[0]=1;
for(int mask=1;mask<states;++mask) for(int last=0;last<n;++last) if(mask>>last&1){
    int added=left[last][mask&(leftStates-1)]+right[last][mask>>half];
    dp[mask]=min(dp[mask],dp[mask^(1<<last)]+added);
}
cout<<dp.back()<<'\n';
    return 0;
}
