#include <bits/stdc++.h>
using namespace std;
long long ways[81][2],ones[81][2];
long long firstOnes(int len,int previous,long long count){
    if(len==0||count==0) return 0;
    long long zero=ways[len-1][0];
    if(previous==1||count<=zero) return firstOnes(len-1,0,count);
    return ones[len-1][0]+(count-zero)+firstOnes(len-1,1,count-zero);
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
ways[0][0]=ways[0][1]=1;
for(int len=1;len<=80;++len) for(int previous=0;previous<2;++previous){
    ways[len][previous]=ways[len-1][0];ones[len][previous]=ones[len-1][0];
    if(previous==0){ways[len][previous]+=ways[len-1][1];ones[len][previous]+=ones[len-1][1]+ways[len-1][1];}
}
long long n;
while(cin>>n){
    long long answer=0;int length=1;
    while(n>=length*ways[length-1][1]){
        n-=length*ways[length-1][1];answer+=ways[length-1][1]+ones[length-1][1];++length;
    }
    long long full=n/length,rank=full;int rest=n%length;
    answer+=full+firstOnes(length-1,1,full);
    if(rest>0){
        ++answer;--rest;int previous=1;
        for(int remaining=length-1;rest>0;--remaining,--rest){
            long long zero=ways[remaining-1][0];int bit=0;
            if(previous==0&&rank>=zero){rank-=zero;bit=1;++answer;}
            previous=bit;
        }
    }
    cout<<answer<<'\n';
}
    return 0;
}
