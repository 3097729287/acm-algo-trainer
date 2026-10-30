#include <bits/stdc++.h>
using namespace std;
char operation[3];
long long solve(const vector<long long>&numbers,int step){
    if(numbers.size()==1)return numbers[0];
    long long answer=LLONG_MAX;int size=(int)numbers.size();
    for(int i=0;i<size;++i)for(int j=i+1;j<size;++j){
        vector<long long>next;for(int k=0;k<size;++k)if(k!=i&&k!=j)next.push_back(numbers[k]);
        // 本层只执行这一时刻的运算，不改变三个运算符的先后。
        next.push_back(operation[step]=='+'?numbers[i]+numbers[j]:numbers[i]*numbers[j]);
        answer=min(answer,solve(next,step+1));
    }
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
vector<long long>numbers(4);for(auto &x:numbers)cin>>x;for(char &c:operation)cin>>c;
cout<<solve(numbers,0)<<'\n';
    return 0;
}
