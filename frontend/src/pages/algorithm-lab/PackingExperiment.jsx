import { useState } from 'react';
import { ArrowRight, Backpack, Check, Flashlight, HeartPulse, Radio } from 'lucide-react';
import { EXPEDITION, EXPEDITION_CAPACITY as CAPACITY, EXPEDITION_OPTIMUM } from './knapsackModel.js';
import { BagSlots, ChoiceCheck, Feedback, Hints } from './LabParts.jsx';
import { KnapsackChoiceFilm } from './KnapsackMotion.jsx';

export default function PackingExperiment(props) {
  const { drafts, updateDraft, onPass } = props;
  const picked = Array.isArray(drafts.packItems) ? drafts.packItems.filter(id => EXPEDITION.some(item => item.id === id)) : [];
  const items = EXPEDITION.filter(item => picked.includes(item.id)), weight = items.reduce((sum, item) => sum + item.weight, 0), value = items.reduce((sum, item) => sum + item.value, 0);
  const [feedback, setFeedback] = useState(''), icons = [Radio, Flashlight, HeartPulse], good = weight <= CAPACITY && value === EXPEDITION_OPTIMUM;
  return <>
    <div className="lab-story"><h2>背包只有 {CAPACITY} 格，你会带走什么？</h2><p>三件装备各一件，不可拆分。点击选择，让总重量不超过 {CAPACITY}，总价值尽可能大。</p></div>
    <div className="lab-pack-layout"><div className="lab-equipment" aria-label="可选装备">{EXPEDITION.map((item, i) => { const Icon = icons[i]; return <button type="button" key={item.id} className="lab-item" aria-label={`${item.id} ${item.name}，重量 ${item.weight}，价值 ${item.value}`} aria-pressed={picked.includes(item.id)} onClick={() => { updateDraft('packItems', picked.includes(item.id) ? picked.filter(id => id !== item.id) : [...picked, item.id]); setFeedback(''); }}><span className="lab-item-icon"><Icon size={26}/></span><span><strong>{item.id} {item.name}</strong><span>重量 {item.weight} · 价值 {item.value}</span></span><span className="lab-item-toggle">{picked.includes(item.id) ? <Check size={16}/> : '+'}</span></button>; })}</div>
      <div className={`lab-bag ${weight > CAPACITY ? 'lab-bag-overflow' : ''}`}><div className="lab-bag-top"><Backpack size={23}/><span>你的背包</span><b>{weight} / {CAPACITY} 格</b></div><BagSlots items={items} capacity={CAPACITY}/><div className="lab-pack-value"><span>总价值</span><strong>{value}</strong></div><button type="button" className="lab-button" onClick={() => { if (good) { onPass('pack'); setFeedback('最优方案：B + C，重量 3 + 2 = 5，价值 5 + 3 = 8，比只拿 A 的 7 更高。'); } else setFeedback(weight > CAPACITY ? `超过 ${CAPACITY} 格了，请取出一件。` : value === 0 ? '先点击装备，试着装一次。' : '装得下。还能找到价值更高的组合吗？'); }}>检查我的方案<ArrowRight size={15}/></button></div></div>
    {feedback && <Feedback good={good}>{feedback}</Feedback>}
    <Hints id="packing" items={['对讲机的价值最高，性价比 7/4 也高于 B 的 5/3 和 C 的 3/2。但它会剩下 1 格。', '比较“只拿 A”和“同时拿 B、C”。物品不能拆开。']} {...props}/>
    <ChoiceCheck id="greedy" title="为什么不能一直挑性价比最高的？" choices={[
      { id: 'ratio', label: '因为性价比算错了', feedback: '7/4 确实大于 5/3 和 3/2，但先拿 A 后，只剩 1 格，B、C 都装不下。' },
      { id: 'combination', label: '整件选择会占住容量，要比较组合', feedback: '对。只拿 A 得到 7，拿 B 和 C 得到 8。需要把“拿”和“不拿”两种选择都考虑到。' },
      { id: 'small', label: '以后总选重量最小的就行', feedback: '若容量 3，两件物品分别是（重量 1，价值 1）和（重量 3，价值 100），先拿小件也会错。' },
    ]} answer="combination" {...props}/>
    <KnapsackChoiceFilm/>
    <p className="lab-caption">每件只能“不拿”或“拿一次”，所以叫 <b>0/1 背包</b>。物品一多，试遍所有组合就很慢。下一节，把小背包的答案记下来重复使用。</p>
  </>;
}
