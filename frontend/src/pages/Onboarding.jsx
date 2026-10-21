import { useEffect, useLayoutEffect, useRef, useState } from 'react';

const STEPS = [
  { page: 'settings', target: '[aria-label="账号与身份"]', title: '连接账号', text: '打开“账号与身份”，展开“公开账号与评分”，填写你的竞赛账号。已有公开 AC 会自动同步；TB 账号负责保存训练数据。可以稍后绑定。' },
  { page: 'library', target: '.list-page .search-box', title: '找到想练的题', text: '输入题名、比赛或知识点；筛选按钮汇总比赛分类、知识点和难度。准备好后，下一步会指引你打开一道题。' },
  { page: 'library', target: '.problem-table tbody tr[data-id] .problem-title', title: '进入练习', text: '点击高亮题名，实际打开一道题。进入工作台后，指引会继续介绍题面、代码和运行。', action: 'open' },
  { practice: true, target: '.wb-statement-pane', title: '阅读题面', text: '先确认题意、输入输出和样例。这里可以切换原文与中文，也可以调整题面字号。' },
  { practice: true, target: '.cm-editor', title: '编写代码', text: '选择 C++17 或 Python 3 后编写代码，草稿会自动保存。上方的保存状态会告诉你是否保存成功。' },
  { practice: true, target: '.wb-run-actions', title: '运行与提交', text: '先用“运行”检查样例，再用“提交”进入原站。首次提交需在浏览器登录并确认；结果显示后自动关闭本次提交窗口，原站 AC 才计入通过数。你可以稍后完成这道题。' },
  { practice: true, target: '.wb-toolbar button[aria-label="返回列表"]', title: '回到题库', text: '点击高亮的返回按钮。草稿会保留，下次打开这道题可以接着写。', action: 'return' },
  { page: 'records', target: '.submission-log', title: '查看提交结果', text: '正式提交后，这里会按日期保存结果。点击记录可以查看当次代码；样例运行结果留在工作台中。' },
  { page: 'mock', target: '.mock-mode-options', title: '组成一场训练', text: '选择综合、专项、随机单题或重现赛，设置题数和时长，再生成预览。确认试卷后才开始计时，结束后复盘。' },
  { page: 'growth', target: '.progress-growth-columns', title: '安排下一次练习', text: '点击知识雷达的专题进入二级知识点，查看掌握程度与推荐题。题单提供从基础思想到迁移练习的学习框架。右下角的日历和奖章分别打开每日任务与成就。' },
  { page: 'settings', target: '.settings-home-grid', title: '完成入门', text: '选择分类进入详细设置，返回时会记住打开位置。点击右上角头像更换图片；数据与帮助里可以导出数据、重新开始指引。' },
];

export default function Onboarding({ onComplete, onNavigate, practiceId }) {
  const [step, setStep] = useState(0), [rect, setRect] = useState(null), [position, setPosition] = useState({});
  const current = STEPS[step], card = useRef(null), callbacks = useRef({ onNavigate, onComplete });
  callbacks.current = { onNavigate, onComplete };
  useEffect(() => { if (current.page) callbacks.current.onNavigate(current.page); }, [step]);
  useEffect(() => {
    const escape = event => { if (event.key === 'Escape') { event.preventDefault(); event.stopImmediatePropagation(); callbacks.current.onComplete(); } };
    document.addEventListener('keydown', escape, true);
    return () => document.removeEventListener('keydown', escape, true);
  }, []);
  useEffect(() => {
    if (current.action === 'open' && practiceId) setStep(3);
    if (current.action === 'return' && !practiceId) setStep(7);
  }, [step, practiceId]);
  useLayoutEffect(() => {
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
  }, [step, practiceId]);
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
  }, [rect, step]);
  const missingPractice = current.practice && !practiceId;
  return <div className="guided-tour" aria-label="新手指引覆盖层">
    {rect && <div className="tour-highlight" style={{ left: rect.left - 5, top: rect.top - 5, width: rect.width + 10, height: rect.height + 10 }} />}
    <section ref={card} className="tour-card" style={position} role="dialog" aria-label="新手指引" aria-modal="false">
      <button className="tour-close" onClick={onComplete}>结束指引 ×</button>
      <small>{step + 1} / {STEPS.length}</small><h3>{current.title}</h3><p>{current.text}</p>
      {missingPractice ? <button onClick={() => setStep(2)}>重新选择练习题</button> : current.action === 'open' && !rect ? <p role="status">没有匹配题目，请清除搜索或筛选。</p> : current.action && <small role="status">请点击高亮的{current.action === 'open' ? '题名' : '返回按钮'}继续</small>}
      <footer><button disabled={!step} onClick={() => setStep(value => value === 7 || value === 3 ? 1 : value - 1)}>上一步</button>
        <button className="primary" disabled={!!current.action || missingPractice} onClick={() => step === STEPS.length - 1 ? onComplete() : setStep(value => value + 1)}>{step === STEPS.length - 1 ? '完成' : '下一步'}</button></footer>
    </section>
  </div>;
}
