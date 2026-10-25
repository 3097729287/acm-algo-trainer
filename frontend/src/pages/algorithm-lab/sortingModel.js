export const SORT_NAMES={bubble:'冒泡排序',insertion:'插入排序',selection:'选择排序',merge:'归并排序',quick:'快速排序',randomQuick:'随机快速排序',bucket:'桶排序',counting:'计数排序',radix:'基数排序'};

export function parseSortInput(text){
 const parts=text.trim().split(/[\s,，]+/);
 if(!text.trim()||parts.length>12||parts.some(x=>!/^\d+$/.test(x)||Number(x)>999))throw Error('输入 1～12 个 0～999 的整数，用空格分隔。');
 return parts.map(Number);
}

export function sortingTrace(values,algorithm='bubble',seed=7){
 if(!SORT_NAMES[algorithm]||!values.length||values.length>12||values.some(x=>!Number.isInteger(x)||x<0||x>999))throw Error('无效的排序实验数据');
 const a=values.map((value,id)=>({value,id})),frames=[];
 let comparisons=0,moves=0,inversions=0,rng=(Number(seed)>>>0)||7;
 const copy=items=>items.map(x=>({...x}));
 const save=(note,active=[],extra={})=>frames.push({items:copy(a),note,active,comparisons,moves,inversions,...extra});
 const swap=(i,j)=>{if(i!==j){[a[i],a[j]]=[a[j],a[i]];moves+=2;}};
 const random=()=>{rng^=rng<<13;rng^=rng>>>17;rng^=rng<<5;return rng>>>0;};
 save('每个数下方的小编号表示它在原数组中的位置；可以用相同的数检查稳定性。');
 if(algorithm==='bubble'){
  for(let end=a.length-1;end>0;end--){let changed=false;
   for(let i=0;i<end;i++){comparisons++;const x=a[i].value,y=a[i+1].value;
    if(x>y){swap(i,i+1);changed=true;save(`${x} > ${y}，交换相邻两项。`,[i,i+1],{range:[0,end+1]});}
    else save(`${x} ≤ ${y}，保持顺序。`,[i,i+1],{range:[0,end+1]});
   }
   save(`本轮最大值已到下标 ${end}；下轮不再检查右侧已排好部分。`,[],{sortedFrom:end});
   if(!changed){save('整轮没有交换，整个数组已经有序，提前结束。');break;}
  }
 }else if(algorithm==='insertion'){
  for(let i=1;i<a.length;i++){let j=i;save(`将下标 ${i} 的数插入左侧有序部分。`,[i],{range:[0,i+1]});
   while(j>0){comparisons++;if(a[j-1].value<=a[j].value){save('左邻居不更大，插入位置已经找到。',[j-1,j]);break;}
    swap(j-1,j);save('当前数向左移动一格，越过一个更大的数。',[j-1,j]);j--;
   }
  }
 }else if(algorithm==='selection'){
  for(let i=0;i<a.length-1;i++){let best=i;
   for(let j=i+1;j<a.length;j++){comparisons++;if(a[j].value<a[best].value)best=j;save(`未排好部分中，当前最小值位于下标 ${best}。`,[best,j],{range:[i,a.length]});}
   swap(i,best);save('把这一轮的最小值放到未排好部分开头。长距离交换可能改变相同值的先后。',[i,best]);
  }
 }else if(algorithm==='merge'){
  const sort=(l,r)=>{if(r-l<2)return;const m=(l+r)>>1;
   save(`把 [${l},${r}) 分成 [${l},${m}) 和 [${m},${r})；先分别排好。`,[],{range:[l,r],split:m});sort(l,m);sort(m,r);
   const left=copy(a.slice(l,m)),right=copy(a.slice(m,r)),buffer=[];let i=0,j=0;
   while(i<left.length&&j<right.length){comparisons++;const takeLeft=left[i].value<=right[j].value;
    if(takeLeft)buffer.push(left[i++]);else{inversions+=left.length-i;buffer.push(right[j++]);}
    save(takeLeft?'取左侧队首；相等时取左边，保持原来的先后。':`右侧队首更小，和左侧剩余 ${left.length-i} 项都构成逆序对。`,[],{range:[l,r],split:m,buffer:copy(buffer)});
   }
   buffer.push(...left.slice(i),...right.slice(j));a.splice(l,r-l,...buffer);moves+=buffer.length;
   save(`合并完成：[${l},${r}) 已有序。`,[],{range:[l,r],buffer:copy(buffer)});
  };sort(0,a.length);
 }else if(algorithm==='quick'||algorithm==='randomQuick'){
  const sort=(l,r)=>{if(r-l<2)return;const chosen=algorithm==='quick'?l:l+random()%(r-l),pivot=a[chosen].value;
   swap(l,chosen);let lt=l,i=l,gt=r;
   save(`选择基准 ${pivot}，把 [${l},${r}) 分成小于、等于和大于它的三段。`,[l],{range:[l,r],pivot});
   while(i<gt){comparisons++;
    if(a[i].value<pivot){swap(lt++,i++);}else{comparisons++;if(a[i].value>pivot){swap(i,--gt);}else i++;}
    save(`小于：[${l},${lt})；等于：[${lt},${i})；未检查：[${i},${gt})；大于：[${gt},${r})。`,i<gt?[i]:[],{range:[l,r],pivot,partition:[lt,i,gt]});
   }
   sort(l,lt);sort(gt,r);
  };sort(0,a.length);
 }else if(algorithm==='counting'){
  const counts=new Map();for(let i=0;i<a.length;i++){const value=a[i].value;counts.set(value,(counts.get(value)||0)+1);save(`数值 ${value} 所在桶的频数加 1。`,[i],{buckets:[...counts].sort((x,y)=>x[0]-y[0]).map(([key,count])=>({key,values:Array(count).fill(key)}))});}
  // Prefix end positions + right-to-left placement retain the order of equals.
  const ends=new Map();let sum=0;for(let key=0;key<=Math.max(...values);key++){sum+=counts.get(key)||0;ends.set(key,sum);}
  const output=Array(a.length).fill(null);
  for(let i=a.length-1;i>=0;i--){const item=a[i],position=ends.get(item.value)-1;ends.set(item.value,position);output[position]=item;moves++;save(`从右向左取 ${item.value}，放到这个值剩余的最后一个位置 ${position}。`,[i],{buffer:output.map(x=>x?{...x}:null)});}
  a.splice(0,a.length,...output);
 }else if(algorithm==='bucket'){
  const width=Math.max(1,Math.ceil((Math.max(...values)+1)/4)),buckets=Array.from({length:4},()=>[]);
  for(let i=0;i<a.length;i++){const k=Math.floor(a[i].value/width);buckets[k].push(a[i]);save(`${a[i].value} 进入范围 [${k*width},${(k+1)*width}) 的桶。`,[i],{buckets:buckets.map((v,j)=>({key:`${j*width}～${(j+1)*width-1}`,values:v.map(x=>x.value)}))});}
  for(let k=0;k<buckets.length;k++){const bucket=buckets[k];for(let i=1;i<bucket.length;i++)for(let j=i;j>0;j--){comparisons++;if(bucket[j-1].value<=bucket[j].value)break;[bucket[j-1],bucket[j]]=[bucket[j],bucket[j-1]];moves+=2;}
   save(`在第 ${k+1} 个桶内插入排序；桶之间的值域本来就有先后。`,[],{buckets:buckets.map((v,j)=>({key:`${j*width}～${(j+1)*width-1}`,values:v.map(x=>x.value)}))});}
  a.splice(0,a.length,...buckets.flat());moves+=a.length;
 }else{
  const max=Math.max(...values);
  for(let place=1;place<=Math.max(1,max);place*=10){const buckets=Array.from({length:10},()=>[]);
   for(let i=0;i<a.length;i++){const digit=Math.floor(a[i].value/place)%10;buckets[digit].push(a[i]);save(`按 ${place===1?'个位':place===10?'十位':'百位'}分桶：${a[i].value} 的这一位是 ${digit}；追加到桶尾。`,[i],{place,buckets:buckets.map((v,key)=>({key,values:v.map(x=>x.value)}))});}
   a.splice(0,a.length,...buckets.flat());moves+=a.length;save(`本轮稳定收集后，低 ${String(place).length} 位已经有序。`,[],{place});
  }
 }
 save('排序完成。比较相同值的小编号，检查它们是否仍按原顺序排列。');
 return frames;
}
