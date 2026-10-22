import { useMemo, useState } from 'react';
import { ArrowRight, Check, Code2, FlaskConical, Play } from 'lucide-react';
import { cppTemplate, displayValue, solveExactly, table01, templateResults, traceKnapsack } from './knapsackModel.js';
import { MISSIONS, RECOGNITION } from './knapsackCourse.js';
import { ChoiceCheck, CodeBlock, Feedback, Hints, NumberCheck } from './LabParts.jsx';

const BUILD_FIELDS = [
  { key: 'init', label: '① 初始状态', options: [['zero', '全部为 0：可以什么都不拿'], ['negative', '只有 dp[0]=0，其余不可达']] },
  { key: 'direction', label: '② 容量循环', options: [['down', '从 W 到 w，逐格递减'], ['up', '从 w 到 W，逐格递增']] },
  { key: 'source', label: '③ 选这件时的来源', options: [['remaining', 'dp[c - w]：给当前物品留出重量'], ['same', 'dp[c]：从当前容量继续加']] },
  { key: 'output', label: '④ 最终答案', options: [['capacity', 'dp[W]：容量上限为 W'], ['count', 'dp[n]：下标使用物品总数']] },
];

export function TemplateWorkshop(props) {
  const { drafts, updateDraft, onPass, passed } = props;
  const config = drafts.builder && typeof drafts.builder === 'object' ? drafts.builder : {};
  const complete = BUILD_FIELDS.every(field => field.options.some(([key]) => key === config[field.key]));
  const [run, setRun] = useState(''), fingerprint = JSON.stringify(config), results = useMemo(() => complete ? templateResults(config) : [], [fingerprint, complete]);
  const visible = run === fingerprint, allGood = results.length > 0 && results.every(test => test.actual === test.expected);
  const diagnosis = config.init !== 'zero' ? '先检查初始化：题目只要求不超过容量，空方案对每个容量上限都合法。' : config.direction !== 'down' ? '一件物品的测试失败了。正序让来源状态包含了当前物品，回到上一节看它被重复使用的位置。' : config.source !== 'remaining' ? '拿一件物品会消耗 w 的容量。来源必须从 c−w 出发，不能凭空增加价值。' : 'dp 的下标表示容量，不表示物品数量。最终应读取 dp[W]，还要确认数组没有越界。';
  return <>
    <div className="lab-story"><span className="lab-eyebrow">把每一行代码和一个理由连起来</span><h2>模板应该是你推出来的。</h2><p>任务仍是：每件最多一次，总重量不超过 W，求最大价值。输入第一行为 n、W，接下来 n 行是重量 w 和价值 v。选择四个关键部分，再让小反例检验它们。</p></div>
    <div className="lab-build-layout"><div className="lab-builder" aria-label="C++ 模板构造器">{BUILD_FIELDS.map(field => <label key={field.key}><span>{field.label}</span><select aria-label={field.label} value={config[field.key] || ''} onChange={event => { updateDraft('builder', { ...config, [field.key]: event.target.value }); setRun(''); }}><option value="">由你决定…</option>{field.options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>)}<button type="button" className="lab-button" disabled={!complete} onClick={() => { setRun(fingerprint); if (allGood) onPass('template'); }}><Play size={15}/>用反例检验模板</button>{passed.template && <small className="lab-completed"><Check size={14}/>曾通过全部教学用例</small>}<p className="lab-caption">这里执行你所选的状态与循环逻辑；任意 C++ 程序请在做题工作台编译运行。</p></div><CodeBlock title="由你的选择生成 · C++17" code={cppTemplate(config)} copy={visible && allGood}/></div>
    {visible && <><div className="lab-panel"><div className="lab-panel-title"><h3>小输入，是给代码提的问题</h3><small>{results.filter(test => test.actual === test.expected).length} / {results.length} 一致</small></div><div className="lab-table-scroll"><table className="lab-test-results"><thead><tr><th>检验什么</th><th>输入（重量, 价值）</th><th>应得</th><th>你的逻辑</th></tr></thead><tbody>{results.map(test => <tr key={test.name}><td>{test.actual === test.expected ? <Check size={15}/> : <FlaskConical size={15}/>} {test.name}</td><td>W={test.capacity}；{test.items.map(item => `(${item.weight}, ${item.value})`).join(' ')}</td><td>{displayValue(test.expected)}</td><td data-correct={test.actual === test.expected}>{displayValue(test.actual)}</td></tr>)}</tbody></table></div></div><Feedback good={allGood}>{allGood ? '四个决定都和状态含义一致。你构造的是“不超过容量”的 0/1 背包模板，可以复制后独立重写一次。' : diagnosis}</Feedback></>}
    <div className="lab-three-notes"><div><Code2 size={20}/><b>复杂度要算出来</b><p>每件物品枚举不超过 W 个容量：时间 O(nW)，空间 O(W)。W 很大时，先停下来检查可行性。</p></div><div><b>价值用 long long</b><p>两件价值 2×10⁹ 的物品，合计已超过 int 的常见上限。dp 和 v 都用 long long。</p></div><div><b>写完先问三句话</b><p>每格表示什么？这次读的是哪一轮？空方案、刚好装下和装不下分别会怎样？</p></div></div>
  </>;
}

const BUGS = [
  { id: 'debug-loop', title: '01 / 一件变成了两件', text: '容量 4；只有一件物品，重量 2、价值 3。每件最多一次，总重量不超过容量。', expected: 3,
    broken: 'for (int c = w; c <= W; ++c)\n    dp[c] = max(dp[c], dp[c - w] + v);',
    fixed: 'for (int c = W; c >= w; --c)\n    dp[c] = max(dp[c], dp[c - w] + v);',
    choices: [['up', '保留正序，只把 dp 改成 long long'], ['down', '改成倒序，保留上一轮的来源状态'], ['bigger', '把容量增大，让重复选择也能放下']], answer: 'down',
    explain: '正序时先有 dp[2]=3，之后 dp[4] 再加一次变成 6。倒序先算 dp[4]，此时 dp[2] 仍为 0，结果才是 3。',
    evaluate: fixed => traceKnapsack([{ id: 'A', weight: 2, value: 3 }], 4, fixed ? 'down' : 'up').values[4] },
  { id: 'debug-exact', title: '02 / 不存在的方案也有价值？', text: '必须恰好装满 3；只有一件重量 2、价值 5 的物品。装不满应该报告不可达。', expected: -Infinity,
    broken: 'vector<long long> dp(W + 1, 0);\nfor (int c = W; c >= w; --c)\n    dp[c] = max(dp[c], dp[c - w] + v);',
    fixed: 'const long long NEG = -(1LL << 60);\nvector<long long> dp(W + 1, NEG);\ndp[0] = 0;\nfor (int c = W; c >= w; --c)\n    if (dp[c - w] != NEG)\n        dp[c] = max(dp[c], dp[c - w] + v);\n// dp[W] == NEG 时报告不可达',
    choices: [['zero', '继续全部初始化为 0，表示没选物品'], ['reachable', '只有 dp[0]=0，其余不可达；先检查来源'], ['up', '把容量改成正序，让它凑满']], answer: 'reachable',
    explain: '重量 1 根本不可达，全 0 却让代码把 dp[1]+5 当成重量 3 的合法方案。恰好装满必须区分“合法且价值 0”和“根本不存在”。',
    evaluate: fixed => fixed ? solveExactly([{ weight: 2, value: 5 }], 3) : table01([{ weight: 2, value: 5 }], 3).at(-1)[3] },
  { id: 'debug-boundary', title: '03 / 恰好能装下，却没选上', text: '容量 2；一件物品重量 2、价值 7。最大价值应为 7，代码却给出 0。', expected: 7,
    broken: 'for (int c = W; c > w; --c)\n    dp[c] = max(dp[c], dp[c - w] + v);',
    fixed: 'for (int c = W; c >= w; --c)\n    dp[c] = max(dp[c], dp[c - w] + v);',
    choices: [['strict', '保留 c > w，等号可能造成越界'], ['inclusive', '改为 c >= w，c-w=0 也是合法来源'], ['init', '把初值都改成物品价值 7']], answer: 'inclusive',
    explain: 'c=w 时，来源是 dp[0]。它对应“先什么都不拿，再加入当前物品”。漏掉等号，就漏掉了恰好能放下的方案。',
    evaluate: fixed => fixed ? table01([{ weight: 2, value: 7 }], 2).at(-1)[2] : 0 },
];

function BugCase({ bug, ...props }) {
  const { drafts, updateDraft, passed, onPass } = props, choice = drafts[bug.id] || '';
  const [tested, setTested] = useState(false), correct = choice === bug.answer, repaired = tested && correct;
  const actual = bug.evaluate(repaired), brokenValue = bug.evaluate(false);
  return <section className="lab-panel lab-bug" aria-label={bug.title}><div className="lab-panel-title"><h3>{bug.title}</h3>{passed[bug.id] && <span className="lab-completed"><Check size={14}/>曾修复</span>}</div><p>{bug.text}</p><div className="lab-bug-outputs"><span>正确结果 <b>{displayValue(bug.expected)}</b></span><span>原代码得到 <b>{displayValue(brokenValue)}</b></span><span>修复后 <b>{tested ? displayValue(actual) : '等待复测'}</b></span></div><CodeBlock title={repaired ? '已修复 · C++17' : '待找错 · C++17'} code={repaired ? bug.fixed : bug.broken}/><form onSubmit={event => { event.preventDefault(); setTested(true); if (correct && bug.evaluate(true) === bug.expected) onPass(bug.id); }}><fieldset><legend>选择一个有依据的修复</legend>{bug.choices.map(([id, label]) => <label key={id} className="lab-choice"><input type="radio" name={bug.id} value={id} checked={choice === id} onChange={() => { updateDraft(bug.id, id); setTested(false); }}/><span>{label}</span></label>)}</fieldset><button type="submit" className="lab-button" disabled={!choice}>应用修复并复测<Play size={15}/></button></form>{tested && <Feedback good={repaired}>{repaired ? bug.explain : '这个修改没有解决状态或边界的根因。先比较“正确结果”和“原代码得到”的差别，追踪是哪一次转移制造了它。'}</Feedback>}</section>;
}

export function DebugWorkshop(props) {
  return <><div className="lab-story"><span className="lab-eyebrow">小数据，会替你把错误说清楚</span><h2>别急着改代码，<br/>先让错误现形。</h2><p>手算一个极小输入，确定应得结果，再追踪第一处不一致。每次只修复一个原因，立即复测。下面三个病例都可以用一件物品暴露问题。</p></div>{BUGS.map(bug => <BugCase key={bug.id} bug={bug} {...props}/>)}<div className="lab-note"><FlaskConical size={21}/><p><b>带走一套排错顺序</b>先读题目的“最多 / 恰好”和“每件 / 无限”；再检查初始化、循环方向、c=w、答案下标；最后检查数组大小、long long 和 O(nW)。大样例看不清时，缩到一件物品。</p></div></>;
}

export function TransferWorkshop(props) {
  return <><div className="lab-story"><span className="lab-eyebrow">题面换了，先找不变的结构</span><h2>看到新题，<br/>先问五个问题。</h2><p>容量不一定叫容量，也可能是时间、预算、人数或目标和。别靠题目里有没有“背包”两个字，先把下面五件事说清楚。</p></div><div className="lab-model-questions">{[['资源', '限制住了什么？'], ['选择', '每个选项的消耗和收益是什么？'], ['次数', '一次、无限次，还是有限次？'], ['目标', '最大、最小、可达，还是计数？'], ['规模', '状态数和复杂度承受得住吗？']].map(([label, text], i) => <div key={label}><b>0{i + 1}</b><strong>{label}</strong><span>{text}</span></div>)}</div>
    <div className="lab-panel"><h3>条件变了，代码也要跟着变</h3><div className="lab-table-scroll"><table className="lab-variant-table"><thead><tr><th>问法</th><th>状态和初值</th><th>依赖关系</th></tr></thead><tbody><tr><td>每件一次，不超过容量，最大价值</td><td>dp[c] 为容量上限 c 的最优值，全 0</td><td>读上一轮，容量倒序</td></tr><tr><td>每件一次，恰好装满，最大价值</td><td>只有 dp[0]=0，其余不可达</td><td>仍然倒序；先检查来源可达</td></tr><tr><td>每种无限，恰好凑钱，最少枚数</td><td>只有 dp[0]=0，其余 INF</td><td>容量正序，可再次使用本种；取 min</td></tr></tbody></table></div><p className="lab-caption">这张表只比较本课涉及的三种问法。计数、有限件、分组等变体需要重新定义状态与转移，不能仅靠更换循环方向。</p></div>
    {RECOGNITION.map(item => <ChoiceCheck key={item.id} {...item} prompt={item.text} {...props}/>)}
  </>;
}

export function PracticeWorkshop(props) {
  const { rows, onTrain, passed } = props;
  const capstone = rows.find(row => !row.catalogHidden && (row.id === '入门赛 50::F' || row.url?.replace(/\/$/, '') === 'https://www.luogu.com.cn/problem/P17162'));
  return <><div className="lab-story"><span className="lab-eyebrow">提示逐步减少，思考由你接手</span><h2>先说清模型，<br/>再把程序写出来。</h2><p>三道课堂任务分别练直接建模、边界改变和题面转化。先独立想，再按需要打开提示。算对答案之后，用上一节的 C++ 模板独立实现；需要恰好装满时，先改状态与初值。</p></div>
    {MISSIONS.map(mission => <div className="lab-mission" key={mission.id}><span className="lab-eyebrow">{mission.tag}</span><NumberCheck {...mission} prompt={mission.text} explanation={mission.takeaway} {...props}/></div>)}
    <div className="lab-panel lab-capstone"><span className="lab-eyebrow">走向真实题目 · 进阶拼接</span><h3>神奇的背包 · 洛谷入门赛 50 F</h3><p>有的物品只有一件，有的有无限件；但无限物品只能选其中一种。把这条新约束和你学过的状态连接起来。</p><p className="lab-caption">先完成课堂任务，再挑战这道组合题。题库中的难度只是参考，它包含额外限制，学习顺序以所需知识为准。</p><Hints id="capstone" items={['先只处理每种只有一件的物品。你已经会计算它们在每个容量上限下的最大价值。', '不能把所有无限物品都正序更新到同一张表，那会混用多种无限物品。每次只考虑其中一种。', '枚举唯一的无限种类 (w,v)，再枚举留给单件物品的容量 c。比较 f[c]+((W-c)/w)*v（整数除法），并保留完全不用无限物品的 f[W]。']} {...props}/>{capstone ? <div className="lab-capstone-actions"><button type="button" className="lab-button" onClick={() => onTrain(capstone.id)}>在 C++ 工作台中练习<ArrowRight size={16}/></button><span>{capstone.accepted ? '原站已通过' : '原站通过情况由训练记录更新'}</span></div> : <p className="lab-caption">本机题库暂未提供这道题。课堂任务可以继续完成，题目收录后会显示工作台入口。</p>}</div>
    <div className="lab-exit-ticket"><Check size={25}/><div><h3>{MISSIONS.every(item => passed[item.id]) ? '你已经完成三次不同的建模。' : '最后带走一张“入手卡”。'}</h3><p>先写一句状态定义 → 找空方案与不可达 → 分“选 / 不选” → 确认来源属于哪一轮 → 算复杂度 → 用一件物品找错。</p><small>课堂自测记录用于安排学习；原站通过与独立解题能力还需要在真实练习中检验。</small></div></div>
  </>;
}
