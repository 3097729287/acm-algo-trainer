import {ArrowDown,ArrowUp,BookOpen,Check,ListPlus,MinusCircle,Star} from 'lucide-react';
import InlineTitle from './InlineTitle.jsx';
import {difficultyBand,difficultyDescription,difficultyLabel} from '@/lib/practiceMetadata.js';
import {verdictLabel,verdictTone} from '@/models/workspaceModel.js';
import {knowledgeLabels} from '@/lib/knowledgeLabels.js';

export function Verdict({value,accepted=false}) {
  const current=value||(accepted?'AC':null);
  return <span className={'verdict '+verdictTone(current)}><span/>{current?verdictLabel(current):<span className="sr-only">未提交</span>}{accepted&&current!=='AC'&&<Check size={11} style={{color:'var(--success)'}} aria-label="曾 AC" title="曾 AC"/>}</span>;
}
export function Difficulty({value,row}) {
  if(row?.difficultyHidden)return <span className="difficulty band-unknown" title={difficultyDescription(row)}>—</span>;
  return <span className={'difficulty band-'+difficultyBand(value)} title={row?difficultyDescription(row):undefined}>{row?difficultyLabel(row):value??'—'}</span>;
}
export function ProblemTableHead({onSort,sorted=false,descending=false}) {
  return <thead><tr><th className="title-head">题目 / 来源</th><th>知识点</th><th>{onSort?<button onClick={onSort}>难度{sorted&&(descending?<ArrowDown size={12}/>:<ArrowUp size={12}/>)}</button>:'难度'}</th><th>提交结果</th><th>最近练习</th><th><span className="sr-only">操作</span></th></tr></thead>;
}
const dateLabel=value=>new Date(value).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
export function ProblemCells({row,favorites=[],showPlatforms=true,busy=false,onTrain,onTag,onFavorite,onSolution,onAddToList,onRemove}) {
  const tags=knowledgeLabels(row),unavailable=!row.id,disabled=busy||unavailable;
  return <>
    <td className="title-cell"><span hidden={!showPlatforms} className={'platform-symbol '+row.platform} title={row.platform}>{row.platform==='牛客'?'牛':row.platform==='洛谷'?'洛':row.platform==='AtCoder'?'At':'CF'}</span><div><button className="problem-title" disabled={disabled} onClick={()=>onTrain(row.id)}><InlineTitle>{row.title}</InlineTitle></button><span className="problem-source">{[row.contest,row.problem].filter(Boolean).join(' · ')}</span></div></td>
    <td className="tags-cell">{tags.slice(0,3).map(tag=>onTag?<button key={tag} className="tag" onClick={()=>onTag({name:tag,tags:[tag]})}>{tag}</button>:<span key={tag} className="tag">{tag}</span>)}{tags.length>3&&<span className="more-tags" title={tags.slice(3).join(' / ')}>+{tags.length-3}</span>}</td>
    <td><Difficulty value={row.difficulty} row={row}/></td><td>{unavailable?<span className="verdict">暂不可用</span>:<Verdict value={row.accepted?'AC':row.verdict} accepted={row.accepted}/>}</td>
    <td className="last-date">{row.lastActivityAt||row.lastSubmittedAt?dateLabel(row.lastActivityAt||row.lastSubmittedAt):row.active?'已加入训练':'—'}</td>
    <td className="row-actions">
      <button className="row-icon" aria-label={'加入题单 '+row.title} title="加入题单" disabled={disabled||!onAddToList} onClick={()=>onAddToList(row.id)}><ListPlus size={15}/></button>
      <button className={'row-icon '+(favorites.includes(row.id)?'favorited':'')} aria-label={(favorites.includes(row.id)?'取消收藏 ':'收藏 ')+row.title} disabled={unavailable||!onFavorite} onClick={()=>onFavorite(row.id)}><Star size={15} fill={favorites.includes(row.id)?'currentColor':'none'}/></button>
      <button className="row-icon" aria-label={'题解 '+row.title} disabled={unavailable||!onSolution||row.solutionAvailable===false||row.locked} onClick={()=>onSolution(row.id)}><BookOpen size={15}/></button>
      {row.active&&onRemove&&<button className="row-icon remove-training" aria-label={'取消训练 '+row.title} disabled={disabled||row.locked} onClick={()=>onRemove(row.id)}><MinusCircle size={15}/></button>}
    </td>
  </>;
}
