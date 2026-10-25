import {useEffect,useRef,useState} from 'react';
import {ArrowLeft,ArrowRight,ExternalLink,List} from 'lucide-react';
import COURSES from '../../../../backend/resources/graph-lab.json';
import GraphExperiment from './GraphExperiment.jsx';
import {matchesGraphProblem} from './graphModel.js';
import {CodeBlock,Feedback} from './LabParts.jsx';
import useCourseKeys from './useCourseKeys.js';
import './graphLab.css';

const CODE={bfs:`vector<int> dist(n, -1), parent(n, -1);
queue<int> q;
dist[start] = 0; q.push(start);
while (!q.empty()) {
    int u = q.front(); q.pop();
    for (int v : adj[u]) if (dist[v] == -1) {
        dist[v] = dist[u] + 1;
        parent[v] = u;
        q.push(v);
    }
}`,dfs:`// 显式递归帧：（当前点，接下来检查的邻边下标）
vector<pair<int,int>> st{{start, 0}};
visited[start] = true;
while (!st.empty()) {
    int u = st.back().first;
    int &next = st.back().second;
    if (next == adj[u].size()) {
        // 所有子分支已完成，可以汇总 u 的子树
        st.pop_back();
        continue;
    }
    int v = adj[u][next++];
    if (visited[v]) continue;
    visited[v] = true;
    parent[v] = u;
    st.push_back({v, 0});
}`,dsu:`// 初始化：iota(parent.begin(), parent.end(), 0);
// size.assign(n, 1);
int find(int x) {
    while (parent[x] != x) {
        parent[x] = parent[parent[x]];
        x = parent[x];
    }
    return x;
}
bool unite(int a, int b) {
    a = find(a); b = find(b);
    if (a == b) return false;
    if (size[a] < size[b]) swap(a, b);
    parent[b] = a;
    size[a] += size[b];
    return true;
}`,dijkstra:`using ll = long long;
const ll INF = (1LL << 62);
vector<ll> dist(n, INF);
vector<int> parent(n, -1);
priority_queue<pair<ll,int>, vector<pair<ll,int>>,
               greater<pair<ll,int>>> pq;
dist[start] = 0; pq.push({0, start});
while (!pq.empty()) {
    auto [du, u] = pq.top(); pq.pop();
    if (du != dist[u]) continue;  // 旧候选
    for (auto [v, w] : adj[u]) {
        if (du + w < dist[v]) {
            dist[v] = du + w;
            parent[v] = u;
            pq.push({dist[v], v});
        }
    }
}`};

function Prediction({label,answer,explanation,saved,onChange}){
 const [checked,setChecked]=useState(false),value=saved||'',correct=value.trim()===String(answer);
 return <form className="lab-check" onSubmit={e=>{e.preventDefault();setChecked(true);}}><label>{label}<input aria-label={label} value={value} maxLength={80} onChange={e=>{setChecked(false);onChange(e.target.value);}}/></label><button className="lab-button" disabled={!value.trim()}>核对推演</button>{checked&&<Feedback good={correct}>{correct?explanation:'暂不一致。先在纸上逐步执行题目规则，区分题目答案和错误写法的输出，再检查一次。'}</Feedback>}</form>;
}
function Guided({problem:p,draft,update,rows,lockedProblems,onTrain,kind}){
 const step=Math.max(0,Math.min(4,Number(draft.step)||0)),steps=['读条件与建模','推演小例','连接代码','反例与迁移','自行实现'];
 const locked=lockedProblems.find(r=>matchesGraphProblem(r,p)),row=rows.find(r=>matchesGraphProblem(r,p));
 return <><h2>{p.pid} · {p.title}</h2><p className="lab-caption">CF 官方 {p.rating} · <a href={p.url} target="_blank" rel="noreferrer">原题<ExternalLink size={12}/></a></p>{locked?<section className="lab-panel"><h3>跟做指导已锁定</h3><p>本题或同源别名正在模拟赛中，交卷后可查看指导。</p><button className="lab-button" onClick={()=>onTrain?.(locked.id)}>返回考场</button></section>:<><nav className="lab-guided-steps" aria-label="解题过程">{steps.map((name,i)=><button key={name} aria-current={step===i?'step':undefined} onClick={()=>update(old=>({...old,step:i,assisted:old.assisted||i===2||i===3}))}>{i+1} {name}</button>)}</nav>
 {step===0&&<><section className="lab-panel"><h3>先把允许的操作与目标说清</h3><p>{p.statement}</p><p className="lab-caption">{p.ranges}</p><label className="seq-code-input">这个问题需要保留哪些状态？<textarea aria-label="我的建模说明" rows={3} value={draft.model||''} onChange={e=>update(old=>({...old,model:e.target.value}))}/></label><p>{p.insight}</p></section></>}
 {step===1&&<><section className="lab-panel"><h3>先算本题的小例</h3><Prediction key={p.pid+'example'} label={p.question} answer={p.answer} explanation={p.calculation} saved={draft.answer} onChange={answer=>update(old=>({...old,answer}))}/><p>题目模型与下方基础图不完全相同。先算上面的题意小例，再用基础图验证遍历或合并规则。</p></section><GraphExperiment kind={kind}/></>}
 {step===2&&<section className="lab-panel"><h3>把关键变化写成一行</h3><p>{p.lineReason}</p><label className="seq-code-input">写出你会使用的关键 C++ 语句<textarea aria-label="关键 C++ 语句" rows={3} value={draft.code||''} onChange={e=>update(old=>({...old,code:e.target.value}))}/></label><button className="lab-button lab-button-quiet" onClick={()=>update(old=>({...old,reference:!old.reference}))}>{draft.reference?'收起参考':'对照参考行'}</button>{draft.reference&&<CodeBlock code={p.line}/>}<p className="lab-caption">这里是教学对照，不是编译评测。等价写法请在工作台运行验证。</p></section>}
 {step===3&&<section className="lab-panel"><h3>执行错误写法，找出第一次偏离</h3><Prediction key={p.pid+'bug'} label={p.bug} answer={p.bugAnswer} explanation={p.bugWhy} saved={draft.bugAnswer} onChange={bugAnswer=>update(old=>({...old,bugAnswer}))}/><label className="seq-code-input">修复依据是什么？哪些条件变化后方法会失效？<textarea rows={3} value={draft.recall||''} onChange={e=>update(old=>({...old,recall:e.target.value}))}/></label></section>}
 {step===4&&<section className="lab-panel"><h3>由你实现完整程序</h3><p>{p.complexity}</p><ul className="seq-checklist">{p.tests.map((item,i)=><li key={item}><label><input type="checkbox" checked={(draft.tested||[]).includes(i)} onChange={()=>update(old=>({...old,tested:(old.tested||[]).includes(i)?old.tested.filter(x=>x!==i):[...(old.tested||[]),i]}))}/>{item}</label></li>)}</ul>{row?<button className="lab-button" onClick={()=>onTrain?.(row.id,{assisted:!!draft.assisted})}>进入工作台自行实现<ArrowRight size={16}/></button>:<a className="lab-button" href={p.url} target="_blank" rel="noreferrer">打开原题实现</a>}<p className="lab-caption">课堂预测与自检不产生 AC。进入代码或查错指导后会保留辅助标记；直接跳去实现不补造辅助记录。</p></section>}</>}</>;
}

export default function GraphCourse({courseId,prefs,setPrefs,rows=[],lockedProblems=[],onTrain,headerActions}){
 const course=COURSES[courseId],saved=prefs.learningPaths?.[courseId]||{},guided=saved.mode==='guided';
 const index=guided?Math.max(0,Math.min(4,Number(saved.guided?.active)||0)):Math.max(0,course.chapters.findIndex(c=>c.id===saved.labV1?.chapter)),count=guided?5:course.chapters.length;
 const chapter=course.chapters[index],problem=course.problems[index],main=useRef(null),menu=useRef(null),toggle=useRef(null),[open,setOpen]=useState(false);
 const patch=fn=>setPrefs(previous=>({...previous,learningPaths:{...previous.learningPaths,[courseId]:fn(previous.learningPaths?.[courseId]||{})}}));
 const navigate=to=>{setOpen(false);patch(old=>guided?{...old,guided:{...old.guided,active:to}}:{...old,labV1:{...old.labV1,chapter:course.chapters[to].id}});};
 const update=fn=>patch(old=>({...old,guided:{...old.guided,problems:{...old.guided?.problems,[problem.pid]:fn(old.guided?.problems?.[problem.pid]||{})}}}));
 useEffect(()=>{main.current.scrollTop=0;main.current.focus({preventScroll:true});},[index,guided]);
 useEffect(()=>{if(!open)return;const close=e=>{if(e.type==='keydown'?e.key==='Escape':!menu.current?.contains(e.target)){if(e.type==='keydown'){e.preventDefault();e.stopPropagation();toggle.current?.focus();}setOpen(false);}};document.addEventListener('pointerdown',close);document.addEventListener('keydown',close);return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',close);};},[open]);
 useCourseKeys({index,count,navigate,menuOpen:open});
 return <div className="algorithm-lab seq-course" aria-label={course.title}><header className="lab-course-header"><h1>{course.title}</h1><span className="lab-position">{guided?'跟做 ':''}{index+1} / {count}</span><aside className="lab-course-tools"><div className="lab-menu" ref={menu}><button type="button" className="lab-menu-toggle" ref={toggle} aria-label="目录" aria-expanded={open} onClick={()=>setOpen(v=>!v)}><List size={17}/>目录</button>{open&&<nav aria-label="课程章节">{(guided?course.problems:course.chapters).map((item,i)=><button key={i} aria-current={i===index?'step':undefined} onClick={()=>navigate(i)}><span>{i+1}</span><b>{item.title}</b></button>)}</nav>}</div><nav className="lab-page-navigation" aria-label="章节翻页"><button className="lab-icon-button" aria-label="上一页" disabled={!index} onClick={()=>navigate(index-1)}><ArrowLeft size={18}/></button><button className="lab-icon-button" aria-label="下一页" disabled={index===count-1} onClick={()=>navigate(index+1)}><ArrowRight size={18}/></button></nav></aside><div className="lab-header-actions">{guided&&<button className="lab-icon-button" aria-label="返回学算法" onClick={()=>patch(old=>({...old,mode:'learn'}))}>课程</button>}{headerActions}</div></header><main className="lab-lesson" ref={main} tabIndex={-1} aria-label={guided?problem.title:chapter.title}>{guided?<Guided key={problem.pid} problem={problem} kind={courseId} draft={saved.guided?.problems?.[problem.pid]||{}} update={update} rows={rows} lockedProblems={lockedProblems} onTrain={onTrain}/>:<><section className="lab-story graph-lesson-copy"><h2>{chapter.title}</h2>{chapter.paragraphs.map(p=><p key={p}>{p}</p>)}</section>{index===5?<CodeBlock code={CODE[courseId]}/>:index<5?<GraphExperiment key={courseId+index} kind={courseId}/>:<section className="lab-panel"><h3>去题目里重新识别模型</h3><p>五题的题面、原站评分和样例已收录。先思考，再推演，最后独立实现。</p><button className="lab-button" onClick={()=>patch(old=>({...old,mode:'guided'}))}>跟着做五道题<ArrowRight size={16}/></button></section>}</>}</main></div>;
}
