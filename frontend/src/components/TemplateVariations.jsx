import Markdown from './SolutionMarkdown.jsx';
import {NotebookPen} from 'lucide-react';
import {matchesTemplateProblem} from '@/lib/templateProblemMatch.js';

export default function TemplateVariations({curriculum,edition='teaching',onTrain,onReference,lockedProblems=[]}){
 if(!curriculum)return null;
 const migration=curriculum.migration;
 const locked=lockedProblems.find(row=>matchesTemplateProblem(row,migration));
 return <div className="template-variations">
  {curriculum.variants.map(variant=><details key={variant.id} className="template-variation"><summary>{variant.title}</summary><Markdown text={variant.markdown}/><Markdown text={'```cpp\n'+(edition==='contest'?variant.contestCode:variant.code)+'\n```'}/></details>)}
  {locked?<p>本题或同源别名正在模拟赛中，交卷后可查看题目迁移指导。</p>:<details className="template-migration" onToggle={event=>{if(event.currentTarget.open)onReference?.(migration.problemId);}}><summary>{migration.title}</summary><Markdown text={migration.markdown}/><a href={migration.url} target="_blank" rel="noreferrer">原题链接 ↗</a>{onTrain&&<button type="button" className="lab-icon-button" aria-label={'实现 '+migration.title} title="实现" onClick={()=>onTrain(migration.problemId,{assisted:true})}><NotebookPen size={17}/></button>}<Markdown text={'```cpp\n'+migration.code+'\n```'}/></details>}
 </div>;
}
