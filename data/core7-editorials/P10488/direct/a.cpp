#include <bits/stdc++.h>
using namespace std;
int n;vector<int>books;
int breaks(){int count=0,previous=0;for(int x:books){if(x!=previous+1)++count;previous=x;}if(previous!=n)++count;return count;}
bool search(int depth,int limit){
    int bad=breaks();if(bad==0)return true;
    if(depth+(bad+2)/3>limit)return false; // 一次操作至多修复三个接缝。
    vector<int>original=books;
    for(int left=0;left<n;++left)for(int middle=left+1;middle<n;++middle)for(int right=middle+1;right<=n;++right){
        vector<int>next;next.reserve(n);
        next.insert(next.end(),original.begin(),original.begin()+left);
        next.insert(next.end(),original.begin()+middle,original.begin()+right);
        next.insert(next.end(),original.begin()+left,original.begin()+middle);
        next.insert(next.end(),original.begin()+right,original.end());
        books=next;
        if(search(depth+1,limit))return true;
        books=original;
    }
    return false;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){cin>>n;books.resize(n);for(int &x:books)cin>>x;bool solved=false;
    for(int limit=0;limit<5;++limit)if(search(0,limit)){cout<<limit<<'\n';solved=true;break;}
    if(!solved)cout<<"5 or more\n";
}
    return 0;
}
