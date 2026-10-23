// Reference programs are used by offline validation and the problem library.
// They are intentionally outside the guided lesson's runtime bundle.
const header = '#include <bits/stdc++.h>\nusing namespace std;\n';
export const REFERENCES = {
  '363B': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n,k;cin>>n>>k;vector<long long> p(n+1);
    for(int i=1;i<=n;++i){long long x;cin>>x;p[i]=p[i-1]+x;}
    long long best=LLONG_MAX;int position=1;
    for(int l=1;l<=n-k+1;++l){
        long long current=p[l+k-1]-p[l-1];
        if(current<best){best=current;position=l;}
    }
    cout<<position<<'\\n';
}`,
  '433B': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n;cin>>n;vector<long long>a(n),p(n+1),q(n+1);
    for(auto &x:a)cin>>x;
    for(int i=0;i<n;++i)p[i+1]=p[i]+a[i];
    vector<long long>b=a;sort(b.begin(),b.end());
    for(int i=0;i<n;++i)q[i+1]=q[i]+b[i];
    int m;cin>>m;while(m--){int type,l,r;cin>>type>>l>>r;
        cout<<(type==1?p[r]-p[l-1]:q[r]-q[l-1])<<'\\n';}
}`,
  '816B': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n,k,q;cin>>n>>k>>q;const int U=200000;
    vector<int>delta(U+2),good(U+1);
    for(int i=0;i<n;++i){int l,r;cin>>l>>r;++delta[l];--delta[r+1];}
    int cover=0;for(int t=1;t<=U;++t){cover+=delta[t];good[t]=good[t-1]+(cover>=k);}
    while(q--){int a,b;cin>>a>>b;cout<<good[b]-good[a-1]<<'\\n';}
}`,
  '295A': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n,m,k;cin>>n>>m>>k;
    vector<long long>a(n+1),d(m+1),times(m+2),delta(n+2);
    vector<int>l(m+1),r(m+1);
    for(int i=1;i<=n;++i)cin>>a[i];
    for(int i=1;i<=m;++i)cin>>l[i]>>r[i]>>d[i];
    while(k--){int x,y;cin>>x>>y;++times[x];--times[y+1];}
    for(int i=1;i<=m;++i){times[i]+=times[i-1];
        delta[l[i]]+=times[i]*d[i];delta[r[i]+1]-=times[i]*d[i];}
    long long add=0;for(int i=1;i<=n;++i){add+=delta[i];cout<<a[i]+add<<(i==n?'\\n':' ');}
}`,
  '276C': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n,q;cin>>n>>q;vector<long long>a(n),delta(n+2),count(n);
    for(auto &x:a)cin>>x;
    while(q--){int l,r;cin>>l>>r;++delta[l];--delta[r+1];}
    long long cover=0;for(int i=1;i<=n;++i){cover+=delta[i];count[i-1]=cover;}
    sort(a.begin(),a.end());sort(count.begin(),count.end());
    long long answer=0;for(int i=0;i<n;++i)answer+=1LL*a[i]*count[i];
    cout<<answer<<'\\n';
}`,
  '381A': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n;cin>>n;vector<int>a(n);for(auto &x:a)cin>>x;
    int l=0,r=n-1,turn=0,score[2]={};
    while(l<=r){if(a[l]>a[r])score[turn]+=a[l++];else score[turn]+=a[r--];turn=1-turn;}
    cout<<score[0]<<' '<<score[1]<<'\\n';
}`,
  '1538C': header + `long long countAtMost(const vector<long long>&a,long long X){
    int l=0,r=(int)a.size()-1;long long answer=0;
    while(l<r){if(a[l]+a[r]<=X){answer+=r-l;++l;}else --r;}
    return answer;
}
int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int tests;cin>>tests;while(tests--){int n;long long L,R;cin>>n>>L>>R;
        vector<long long>a(n);for(auto &x:a)cin>>x;sort(a.begin(),a.end());
        cout<<countAtMost(a,R)-countAtMost(a,L-1)<<'\\n';}
}`,
  '279B': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n;long long t;cin>>n>>t;vector<long long>a(n);for(auto &x:a)cin>>x;
    int l=0,answer=0;long long sum=0;
    for(int r=0;r<n;++r){sum+=a[r];while(sum>t)sum-=a[l++];answer=max(answer,r-l+1);}
    cout<<answer<<'\\n';
}`,
  '580B': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n;long long d;cin>>n>>d;vector<pair<long long,long long>>friends(n);
    for(auto &p:friends)cin>>p.first>>p.second;sort(friends.begin(),friends.end());
    int l=0;long long sum=0,answer=0;
    for(int r=0;r<n;++r){sum+=friends[r].second;
        while(friends[r].first-friends[l].first>=d)sum-=friends[l++].second;
        answer=max(answer,sum);}
    cout<<answer<<'\\n';
}`,
  '701C': header + `int main(){
    ios::sync_with_stdio(false);cin.tie(nullptr);
    int n;string s;cin>>n>>s;int count[256]={},need=0,have=0;
    bool seen[256]={};for(unsigned char c:s)if(!seen[c]){seen[c]=true;++need;}
    int l=0,answer=n;
    for(int r=0;r<n;++r){unsigned char c=s[r];if(count[c]++==0)++have;
        while(have==need){answer=min(answer,r-l+1);unsigned char old=s[l++];if(--count[old]==0)--have;}}
    cout<<answer<<'\\n';
}`,
};

export const OFFICIAL_SAMPLES = {
  '363B': [['7 3\n1 2 6 1 1 7 1\n', '3']],
  '433B': [['6\n6 4 2 7 2 7\n3\n2 3 6\n1 3 4\n1 1 6\n', '24\n9\n28'], ['4\n5 5 2 3\n10\n1 2 4\n2 1 4\n1 1 1\n2 1 4\n2 1 2\n1 1 1\n1 3 3\n1 1 3\n1 4 4\n1 2 2\n', '10\n15\n5\n15\n5\n5\n2\n12\n3\n5']],
  '816B': [['3 2 4\n91 94\n92 97\n97 99\n92 94\n93 97\n95 96\n90 100\n', '3\n3\n0\n4'], ['2 1 1\n1 1\n200000 200000\n90 100\n', '0']],
  '295A': [['3 3 3\n1 2 3\n1 2 1\n1 3 2\n2 3 4\n1 2\n1 3\n2 3\n', '9 18 17'], ['1 1 1\n1\n1 1 1\n1 1\n', '2'], ['4 3 6\n1 2 3 4\n1 2 1\n2 3 2\n3 4 4\n1 2\n1 3\n2 3\n1 2\n1 3\n2 3\n', '5 18 31 20']],
  '276C': [['3 3\n5 3 2\n1 2\n2 3\n1 3\n', '25'], ['5 3\n5 2 4 1 3\n1 5\n2 3\n2 3\n', '33']],
  '381A': [['4\n4 1 2 10\n', '12 5'], ['7\n1 2 3 4 5 6 7\n', '16 12']],
  '1538C': [['4\n3 4 7\n5 1 2\n5 5 8\n5 1 2 4 3\n4 100 1000\n1 1 1 1\n5 9 13\n2 5 5 1 1\n', '2\n7\n0\n1']],
  '279B': [['4 5\n3 1 2 1\n', '3'], ['3 3\n2 2 3\n', '1']],
  '580B': [['4 5\n75 5\n0 100\n150 20\n75 1\n', '100'], ['5 100\n0 7\n11 32\n99 10\n46 8\n87 54\n', '111']],
  '701C': [['3\nAaA\n', '2'], ['7\nbcAAcbc\n', '3'], ['6\naaBCCe\n', '5']],
};
