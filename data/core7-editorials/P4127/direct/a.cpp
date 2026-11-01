#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long low,high;cin>>low>>high;string a=to_string(low-1),b=to_string(high);int digits=b.size();
vector<int>left(digits),right(digits);for(int i=0;i<int(a.size());++i) left[digits-a.size()+i]=a[i]-'0';for(int i=0;i<digits;++i) right[i]=b[i]-'0';
long long answer=0;
for(int target=1;target<=9*digits;++target){
    int width=target+1,layer=width*target;
    vector<long long>ways(digits*layer);ways[0]=1;
    vector<array<int,10>>nextRemainder(target);for(int r=0;r<target;++r) for(int d=0;d<10;++d) nextRemainder[r][d]=(r*10+d)%target;
    vector<int>power10(digits,1%target);for(int len=1;len<digits;++len) power10[len]=power10[len-1]*10%target;
    for(int len=0;len+1<digits;++len){
        for(int sum=0;sum<=min(target,9*len);++sum) for(int r=0;r<target;++r){
            long long count=ways[len*layer+sum*target+r];if(!count) continue;
            for(int d=0;d<=9&&sum+d<=target;++d) ways[(len+1)*layer+(sum+d)*target+nextRemainder[r][d]]+=count;
        }
    }
    auto prefix=[&](const vector<int>&bound){
        long long count=0;int sum=0,remainder=0;
        for(int pos=0;pos<digits;++pos){
            int len=digits-pos-1;
            for(int d=0;d<bound[pos];++d){
                int need=target-sum-d;if(need<0||need>9*len) continue;
                int head=nextRemainder[remainder][d];int tail=(target-head*power10[len]%target)%target;
                count+=ways[len*layer+need*target+tail];
            }
            sum+=bound[pos];remainder=nextRemainder[remainder][bound[pos]];if(sum>target) return count;
        }
        return count+(sum==target&&remainder==0);
    };
    answer+=prefix(right)-prefix(left);
}
cout<<answer<<'\n';
    return 0;
}
