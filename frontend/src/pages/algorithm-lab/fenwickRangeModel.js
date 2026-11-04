export function rangeFenwick(values,operations=[],end=values.length){
 const n=values.length;if(!n||n>12||values.some(x=>!Number.isSafeInteger(x)||Math.abs(x)>1e6))throw Error('数组需要 1–12 个整数，绝对值不超过 1000000。');
 if(!Number.isInteger(end)||end<0||end>n)throw Error('前缀长度须在 0 到数组长度之间。');
 const b1=Array(n+1).fill(0),b2=Array(n+1).fill(0),a=[...values];
 const point=(index,delta)=>{for(let p=index+1;p<=n;p+=p&-p){b1[p]+=delta;b2[p]+=index*delta;}};
 values.forEach((v,i)=>point(i,v-(values[i-1]||0)));
 for(const [l,r,delta] of operations){if(![l,r,delta].every(Number.isSafeInteger)||l<0||l>r||r>n||Math.abs(delta)>1e6)throw Error('区间使用 [l,r)，0 ≤ l ≤ r ≤ n。');if(l===r)continue;point(l,delta);point(r,-delta);for(let i=l;i<r;i++)a[i]+=delta;}
 const path=[];let differencePrefix=0,weightedPrefix=0;
 for(let p=end;p>0;p-=p&-p){path.push(p);differencePrefix+=b1[p];weightedPrefix+=b2[p];}
 return {a,b1,b2,path,difference:a.map((x,i)=>x-(a[i-1]||0)),differencePrefix,weightedPrefix,sum:end*differencePrefix-weightedPrefix,end};
}
