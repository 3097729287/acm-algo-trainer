import { ChevronRight, FileText, Folder, House } from 'lucide-react';
import Tooltip from './Tooltip.jsx';
import './CatalogExplorer.css';

export function CatalogPath({scope,onChange}) {
  return <nav className="catalog-path" aria-label="题目浏览路径"><Tooltip text="全部平台"><button aria-label="全部平台" onClick={()=>onChange({stage:'platforms',platform:'',contest:''})}><House size={16}/></button></Tooltip>{scope.platform&&<><ChevronRight size={13}/><button onClick={()=>onChange({stage:'contests',platform:scope.platform,contest:''})}>{scope.platform}</button></>}{scope.contest&&<><ChevronRight size={13}/><span>{scope.contest}</span></>}{scope.stage==='problems'&&!scope.contest&&<><ChevronRight size={13}/><span>全部题目</span></>}</nav>;
}
export default function CatalogExplorer({rows,scope,onChange}) {
  const platforms=['Codeforces','AtCoder','牛客','洛谷'];
  const groups=new Map();
  if(scope.stage==='contests')for(const row of rows){const name=row.contest || '其他题目';if(!groups.has(name))groups.set(name,[]);groups.get(name).push(row);}
  const entries=scope.stage==='platforms'?platforms.map(name=>({name,count:rows.filter(row=>row.platform===name).length})):Array.from(groups,([name,items])=>({name,count:items.length})).sort((left,right)=>left.name.localeCompare(right.name,'zh-CN',{numeric:true}));
  return <section className="catalog-explorer" aria-label="题库层级浏览"><button className="catalog-folder-row catalog-all-problems" onClick={()=>onChange({...scope,stage:'problems',contest:''})}><FileText size={19}/><strong>全部题目</strong><span>{rows.length}</span><ChevronRight size={16}/></button>{entries.map(item=><button className="catalog-folder-row" key={item.name} disabled={!item.count} aria-label={`打开${scope.stage==='platforms'?'平台':'比赛'} ${item.name}`} onClick={()=>onChange(scope.stage==='platforms'?{stage:'contests',platform:item.name,contest:''}:{...scope,stage:'problems',contest:item.name})}><Folder size={20}/><strong>{item.name}</strong><span>{item.count}</span><ChevronRight size={16}/></button>)}{!entries.length&&<p className="progress-muted">没有匹配的比赛。</p>}</section>;
}
