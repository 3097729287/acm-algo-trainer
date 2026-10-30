import {useMemo,useState} from 'react';
import {ArrowLeft,ArrowRight,Check,GitMerge,Play,RotateCcw} from 'lucide-react';
import {parseXorInput,subsetXors,xorBasis,xorContains,xorKth,xorQuery} from './linearBasisModel.js';
import {Feedback} from './LabParts.jsx';

const Button=({label,children,...props})=><button type="button" className="lab-icon-button" aria-label={label} title={label} {...props}>{children}</button>;
export default function LinearBasisExperiment({draft={},update}) {
 const [input,setInput]=useState(draft.input||'6 5 3'),[target,setTarget]=useState(draft.target||'7'),[merge,setMerge]=useState('1'),[k,setK]=useState(draft.k||'1'),[error,setError]=useState(''),[prediction,setPrediction]=useState(''),[checked,setChecked]=useState(false);
 const parsed=useMemo(()=>{try{return parseXorInput(draft.input||'6 5 3');}catch{return [6n,5n,3n];}},[draft.input]);
 const model=useMemo(()=>xorBasis(parsed),[parsed]),results=useMemo(()=>subsetXors(parsed),[parsed]);
 const index=Math.max(0,Math.min(model.frames.length-1,Number(draft.frame)||0)),frame=model.frames[index],basis=frame.basis;
 const [mode,setMode]=useState('max');
 let query=0n,queryError='';try{query=parseXorInput(target)[0];if(target.trim().split(/[\s,，]+/).length!==1)throw Error();}catch{queryError='查询值须是一个无符号 64 位整数。';}
 const greedy=xorQuery(model.p,query,mode==='min');
 let kth=null;try{if(/^\d+$/.test(k))kth=xorKth(model.p,BigInt(k));}catch{}
 const save=patch=>update({...draft,...patch});
 const apply=()=>{try{parseXorInput(input);save({input,frame:0});setError('');setChecked(false);}catch(e){setError(e.message);}};
 const combine=()=>{try{const extra=parseXorInput(merge),all=[...parsed,...extra];if(all.length>10)throw Error('合并演示最多保留 10 个原数。');const text=all.join(' ');setInput(text);save({input:text,frame:0});setError('');setChecked(false);}catch(e){setError(e.message);}};
 return <section className="lab-panel operations-experiment xor-experiment" aria-label="线性基操作实验">
  <div className="operations-input"><label>原数（每个下标可选一次）<input aria-label="线性基原数" value={input} onChange={e=>setInput(e.target.value)}/></label><Button label="应用数据" onClick={apply}><Check size={17}/></Button><Button label="重置实验" onClick={()=>{setInput('6 5 3');save({input:'6 5 3',frame:0});setError('');setChecked(false);}}><RotateCcw size={17}/></Button></div>{error&&<p role="alert">{error}</p>}
  <p>当前原数 [{parsed.join(', ')}]。0 是空子集的异或值；一个原数不能因为经过多步消元就被选多次。</p>
  <div className="operations-controls"><Button label="上一步" disabled={!index} onClick={()=>save({frame:index-1})}><ArrowLeft size={17}/></Button><Button label="下一步" disabled={index===model.frames.length-1} onClick={()=>save({frame:index+1})}><ArrowRight size={17}/></Button><Button label="查看结果" onClick={()=>save({frame:model.frames.length-1})}><Play size={17}/></Button></div>
  <p aria-live="polite">插入第 {frame.index+1} 个原数 {String(frame.original)}：{frame.action}{frame.before!=null?`，${frame.before} XOR ${frame.pivot} = ${frame.x}`:`，剩余 ${frame.x}`}。当前秩 {frame.rank}。</p>
  <div className="operations-table"><table aria-label="主元与二进制"><thead><tr><th>最高位 i</th><th>p[i] 十进制</th><th>二进制（右端是第 0 位）</th></tr></thead><tbody>{basis.map((x,i)=>x?<tr key={i} data-active={i===frame.bit}><th>{i}</th><td>{String(x)}</td><td><code>{x.toString(2).padStart(4,'0')}</code></td></tr>:null).reverse()}{!frame.rank&&<tr><td colSpan={3}>尚无非零主元</td></tr>}</tbody></table></div>
  <form className="operations-predict" onSubmit={e=>{e.preventDefault();setChecked(true);}}><label>先预测最终有多少个不同异或值<input aria-label="预测不同异或值个数" value={prediction} onChange={e=>{setPrediction(e.target.value);setChecked(false);}}/></label><Button type="submit" label="核对预测" disabled={!prediction.trim()}><Check size={17}/></Button></form>
  {checked&&<Feedback good={prediction.trim()===String(results.length)}>{prediction.trim()===String(results.length)?`秩为 ${model.rank}，不同结果数 2^${model.rank}=${results.length}；${parsed.length} 个下标共有 2^${parsed.length} 种选择。`:'别把下标选择方案数当作不同结果数。独立主元每增加一个，才把可表示集合扩展一倍。'}</Feedback>}
  <details><summary>枚举小例核对</summary><p>全部不同结果：{results.map(String).join(', ')}。</p><p>每个结果对应 {String(1n<<BigInt(parsed.length-model.rank))} 份下标方案；{parsed.length>model.rank?'存在':'不存在'}非空子集异或为 0。</p></details>
  <div className="operations-input"><label>待查询值 / seed<input aria-label="查询异或值" value={target} onChange={e=>{setTarget(e.target.value);save({target:e.target.value});}}/></label><label>最值<select aria-label="异或查询目标" value={mode} onChange={e=>setMode(e.target.value)}><option value="max">最大</option><option value="min">最小</option></select></label></div>
  {queryError?<p role="alert">{queryError}</p>:<><p>{String(query)} {xorContains(model.p,query)?'可以':'不能'}由原数的一个子集表示。seed={String(query)} 时{mode==='max'?'最大':'最小'}异或为 {String(greedy.answer)}。</p><div className="operations-table"><table aria-label="高位贪心过程"><thead><tr><th>主元位</th><th>原答案</th><th>异或候选</th><th>是否采用</th></tr></thead><tbody>{greedy.steps.map(s=><tr key={s.bit}><th>{s.bit}</th><td>{String(s.before)}</td><td>{String(s.before)} XOR {String(s.pivot)} = {String(s.candidate)}</td><td>{s.take?'采用':'保留'}</td></tr>)}</tbody></table></div></>}
  <div className="operations-input"><label>不同结果的下标 k（从 0 开始）<input aria-label="第 k 小下标" value={k} onChange={e=>{setK(e.target.value);save({k:e.target.value});}}/></label><output aria-label="第 k 小结果">{kth===null?'下标越界或无效':String(kth)}</output></div>
  <div className="operations-input"><label>另一组原数<input aria-label="待合并线性基" value={merge} onChange={e=>setMerge(e.target.value)}/></label><Button label="合并线性基" onClick={combine}><GitMerge size={17}/></Button></div>
 </section>;
}
