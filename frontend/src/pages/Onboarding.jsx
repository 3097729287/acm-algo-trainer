import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import {GUIDE_LABELS,PAGE_GUIDES} from '@/lib/guideCatalog.js';
import {PAGE_UNLOCKS} from '@/lib/featureUnlocks.js';
const unlockSummary=[2,3,4,5].map(level=>`Lv.${level}：${PAGE_UNLOCKS.filter(item=>!item.always&&item.level===level).map(item=>item.label).join('、')}`).join('；');

const STEPS = [
  {page:'training-lists',target:'.sidebar nav',title:'按等级逐步开放',text:`先从编程基础题单开始。${unlockSummary}。提交记录与设置一直保留；达到等级后才出现对应板块和指引，设置中的导航可以隐藏可选板块。`},
  {page:'mine',target:'.next-actions',title:'下一步推荐做的事',text:'推荐根据真实待办、独立作答记录、题面可用情况和学习进度产生。每项都列出原因，可继续复习、学算法，或做当前学习阶段的题目。'},
  { page: 'mine', target: '.brand-mark', title: '收起与展开侧边栏', text: '点击左上角 ToBe 标识收起或展开侧边栏。收起后仍可点击导航图标，给题目和图表留出更多空间。' },
  { page: 'mine', target: '.topbar .profile-overview', title: '连接账号', text: '点击右上角昵称打开账号弹窗，可以修改昵称、密码和四个平台账号。专用浏览器会识别已登录的账号；缺少登录时依次打开各站登录页。' },
  { page: 'library', target: '.topbar .search-box', title: '找到想练的题', text: '输入题名、比赛或知识点；筛选按钮汇总比赛分类、知识点和难度。上下箭头切换顺序，选中的知识点可单独取消。下一步会指引你打开一道题。' },
  { page: 'library', target: '.problem-table tbody tr[data-id] .problem-title', title: '进入练习', text: '点击高亮题名，实际打开一道题。进入工作台后，指引会继续介绍题面、代码和运行。', action: 'open' },
  { practice: true, target: '.wb-statement-pane', title: '阅读题面', text: '先确认题意、输入输出和样例。这里可以切换原文与中文，也可以调整题面字号。' },
  { practice: true, target: '.cm-editor', title: '编写代码', text: '选择 C++17 或 Python 3 后编写代码。语言旁的模板选择器可切换初始代码，默认项显示“默认”；自定义初始代码在设置中保存。草稿自动保存，已有草稿再次打开时会保留。' },
  { practice: true, target: '.wb-run-actions', title: '运行与提交', text: '先用“运行”检查样例，再用“提交”进入原站。首次提交需在浏览器登录并确认；结果显示后自动关闭本次提交窗口，原站 AC 才计入通过数。你可以稍后完成这道题。' },
  { practice: true, target: '.wb-toolbar button[aria-label="返回列表"]', title: '回到题库', text: '点击高亮的返回按钮。草稿会保留，下次打开这道题可以接着写。', action: 'return' },
  { page: 'records', target: '.submission-log', title: '查看提交结果', text: '正式提交后，这里会按日期保存结果。点击记录可以查看当次代码；样例运行结果留在工作台中。' },
  { page: 'mock', target: '.mock-mode-options', title: '组成一场训练', text: '选择综合、专项或重现赛，设置题数和时长，再生成预览。确认试卷后才开始计时，结束后复盘。' },
  { page: 'growth', target: '.progress-growth-columns', title: '安排下一次练习', text: '点击一级雷达圆点进入子知识点，Esc 返回；二级知识点可筛选题目。?% 表示作答证据不足。目标计划安排后续练习，日历和奖章打开每日任务与成就。经验等级与能力段位分别成长。' },
  { page: 'mine', target: '.contest-calendar-button', title: '查看比赛日历', text: '底部时钟日历图标打开即将开始的基础比赛。赛程按北京时间排列，点击一场比赛前往原站。旁边的日历用于领取每日任务。' },
  { page: 'settings', target: '.settings-home-grid', title: '完成入门', text: '点击头像可以更换图片。设置中可调整外观、导航与快捷键；新手指引直接列出入门总览和已开放页面的图标，点击对应图标可继续了解操作。' },
];

export default function Onboarding({ onComplete, onNavigate, onDirectory, onShown, practiceId,initialGuide='overview',availablePages }) {
  const [guide]=useState(initialGuide);
  const [step, setStep] = useState(0), [rect, setRect] = useState(null), [position, setPosition] = useState({});
  const allowed=id=>!availablePages||availablePages.includes(id),source=guide==='overview'?STEPS:PAGE_GUIDES[guide]||[];
  const steps=source.map(item=>guide==='overview'&&item.page==='library'&&!allowed('library')&&allowed('training-lists')?{...item,page:'training-lists',target:item.action==='open'?'.training-list-content .problem-title':'.training-list-content',title:item.action==='open'?'进入第一道练习':'打开编程基础题单',text:item.action==='open'?'逐层打开基础题单，点击题名进入工作台。阅读题面、写代码、运行样例与原站提交在 Lv.1 即可使用。':'先选择编程基础中的专题，再打开题目；从输入输出、分支与循环开始，已有代码和通过记录会保留。'}:guide==='overview'&&item.action==='return'&&!allowed('library')?{...item,title:'回到题单'}:item).filter(item=>(!item.page||allowed(item.page))&&(!item.practice||allowed('library')||allowed('training-lists'))&&(!item.target.includes('contest-calendar')||allowed('competitions'))),current=steps[step],card = useRef(null), callbacks = useRef({ onNavigate, onComplete });
  callbacks.current = { onNavigate, onComplete,onShown,guide };
  useEffect(()=>{callbacks.current.onShown?.();},[]);
  const finish=()=>onComplete(guide==='overview');
  useEffect(() => { if (current?.page) callbacks.current.onNavigate(current.page,current.tab);card.current?.querySelector('h3')?.focus({preventScroll:true}); }, [step,guide]);
  useEffect(() => {
    const escape = event => { if (event.key === 'Escape') { event.preventDefault(); event.stopImmediatePropagation(); callbacks.current.onComplete(callbacks.current.guide==='overview'); } };
    document.addEventListener('keydown', escape, true);
    return () => document.removeEventListener('keydown', escape, true);
  }, []);
  useEffect(() => {
    if (current?.action === 'open' && practiceId) setStep(current.nextIndex??step+1);
    if (current?.action === 'return' && !practiceId) setStep(current.nextIndex??step+1);
  }, [step, practiceId,guide]);
  useLayoutEffect(() => {
    if(!current){setRect(null);return;}
    let frame, lastTarget;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const element = [...document.querySelectorAll(current.target)].find(node => node.getBoundingClientRect().height > 0);
        if (element && element !== lastTarget) { element.scrollIntoView({ block: 'nearest', inline: 'nearest' }); lastTarget = element; }
        const bounds = element?.getBoundingClientRect();
        const next = bounds?.width && bounds?.height ? { left: bounds.left, top: bounds.top, width: bounds.width, height: bounds.height } : null;
        setRect(previous => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
      });
    };
    const observer = new MutationObserver(update);
    observer.observe(document.querySelector('.app-shell') || document.body, { subtree: true, childList: true, attributes: true });
    window.addEventListener('resize', update); window.addEventListener('scroll', update, true); update();
    return () => { cancelAnimationFrame(frame); observer.disconnect(); window.removeEventListener('resize', update); window.removeEventListener('scroll', update, true); };
  }, [step, practiceId,guide]);
  useLayoutEffect(() => {
    if (!card.current) return;
    const { width, height } = card.current.getBoundingClientRect(), gap = 18;
    let left = innerWidth - width - gap, top = innerHeight - height - 54;
    if (rect) {
      if (rect.left + rect.width + width + 2 * gap <= innerWidth) { left = rect.left + rect.width + gap; top = rect.top; }
      else if (rect.left >= width + 2 * gap) { left = rect.left - width - gap; top = rect.top; }
      else if (rect.top + rect.height + height + 2 * gap <= innerHeight) top = rect.top + rect.height + gap;
      else if (rect.top >= height + 2 * gap) top = rect.top - height - gap;
    }
    setPosition({ left: Math.max(gap, Math.min(left, innerWidth - width - gap)), top: Math.max(gap, Math.min(top, innerHeight - height - gap)) });
  }, [rect, step,guide]);
  const missingPractice = current?.practice && !practiceId;
  if(!current)return null;
  return <div className="guided-tour" aria-label="新手指引覆盖层">
    {rect && <div className="tour-highlight" style={{ left: rect.left - 5, top: rect.top - 5, width: rect.width + 10, height: rect.height + 10 }} />}
    <section ref={card} className="tour-card" style={position} role="dialog" aria-label="新手指引" aria-modal="false">
      <button className="tour-close" onClick={finish}>结束指引 ×</button>
      <small>{guide==='overview'?'入门总览':GUIDE_LABELS[guide]} · {step + 1} / {steps.length}</small><h3 tabIndex={-1}>{current.title}</h3><p>{current.text}</p>
      {missingPractice ? <button onClick={() => setStep(Math.max(0,steps.findIndex(item=>item.action==='open')))}>重新选择练习题</button> : current.action === 'open' && !rect ? <p role="status">{current.page==='training-lists'?'先打开基础题单，再点击题名。':'没有匹配题目，请清除搜索或筛选。'}</p> : current.action && <small role="status">请点击高亮的{current.action === 'open' ? '题名' : '返回按钮'}继续</small>}
      <button className="tour-directory-button" onClick={onDirectory}>各页指引目录</button>
      <footer><button disabled={!step} onClick={() => setStep(value => {let previous=value-1;while(previous>0&&((steps[previous].practice&&!practiceId)||(steps[previous].action==='return'&&!practiceId)||(steps[previous].action==='open'&&practiceId)))previous--;return Math.max(0,previous);})}>上一步</button>
        <button className="primary" disabled={!!current.action || missingPractice} onClick={() => step === steps.length - 1 ? finish() : setStep(value => value + 1)}>{step === steps.length - 1 ? '完成' : '下一步'}</button></footer>
    </section>
  </div>;
}
