import { useState } from 'react';
import { ArrowLeft, ArrowRight, CalendarDays, Check, Code2, Library, UserRound } from 'lucide-react';

const STEPS = [
  { icon: UserRound, title: '连接你的竞赛账号', text: '在「成长与能力」绑定平台账号。已有的公开 AC 记录会自动同步。', hint: 'TB 账号保存训练数据；原站提交使用浏览器中的网站账号。' },
  { icon: Library, title: '选择一道题', text: '在题库搜索比赛、题名或知识点。点击题目整行进入练习，也可以开始一场模拟赛。', hint: '「我的训练」汇总今日目标、补题与复习。' },
  { icon: Code2, title: '编写、运行、提交', text: '草稿自动保存。先运行样例，再点「提交」打开原站；首次使用时在专用浏览器登录。', hint: '样例通过只验证样例；原站确认 AC 后才计入成绩。' },
  { icon: CalendarDays, title: '按目标持续练习', text: '每日任务收集目标题目并发放经验。完成任务后点击领取；目标可在成长页调整。', hint: '随时从「偏好设置 → 数据与帮助」重看指引或导出 JSON。' },
];

export default function Onboarding({ onComplete }) {
  const [step, setStep] = useState(0);
  const current = STEPS[step], Icon = current.icon;
  return <div className="onboarding">
    <div className="onboarding-art" aria-hidden="true"><Icon size={44}/><span>TB</span></div>
    <div className="onboarding-dots" aria-label={`第 ${step + 1} 步，共 ${STEPS.length} 步`}>{STEPS.map((_, index) => <i key={index} data-active={index === step}/>)}</div>
    <div className="onboarding-step" key={step}><h3>{current.title}</h3><p>{current.text}</p><small>{current.hint}</small></div>
    <footer><button className="text-button" disabled={!step} onClick={() => setStep(value => value - 1)}><ArrowLeft size={15}/>上一步</button><span>{step + 1} / {STEPS.length}</span><button className="primary" onClick={() => step === STEPS.length - 1 ? onComplete() : setStep(value => value + 1)}>{step === STEPS.length - 1 ? <Check size={15}/> : <ArrowRight size={15}/>}{step === STEPS.length - 1 ? '开始训练' : '下一步'}</button></footer>
  </div>;
}
