#include <bits/stdc++.h>
using namespace std;
int n,position[15];bool column[15],downward[30],upward[30];long long solutions=0;
void place(int row){
    if(row==n){
        if(solutions<3)for(int i=0;i<n;++i)cout<<position[i]+1<<(i+1==n?'\n':' ');
        ++solutions;return;
    }
    for(int c=0;c<n;++c)if(!column[c]&&!downward[row+c]&&!upward[row-c+n]){
        position[row]=c;column[c]=downward[row+c]=upward[row-c+n]=true;
        place(row+1);
        column[c]=downward[row+c]=upward[row-c+n]=false; // 完整撤销本行占用。
    }
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
cin>>n;place(0);cout<<solutions<<'\n';
    return 0;
}
