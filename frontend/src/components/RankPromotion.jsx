import {useEffect, useRef, useState} from 'react';
import {createPortal} from 'react-dom';
import {X} from 'lucide-react';
import TierIcon from './TierIcon.jsx';
import {TIER_NAMES} from '@/lib/rankTiers.js';
import './RankPromotion.css';

const COLOURS = ['#bac7d8', '#dfad89', '#c3eaff', '#f4d078', '#77efd1', '#8ed8ff', '#d8a9ff', '#ffa58d', '#f7dc9b'];
const SPARKS = Array.from({length: 24}, (_, i) => {
  const angle = i * Math.PI * (3 - Math.sqrt(5)), radius = 120 + (i % 5) * 22;
  return {'--spark-x': `${Math.cos(angle) * radius}px`, '--spark-y': `${Math.sin(angle) * radius * .8}px`, '--spark-delay': `${950 + i % 6 * 24}ms`};
});
export default function RankPromotion({notice, motion = true, onPresented, onClose}) {
  const root = useRef(null), focus = useRef(document.activeElement), handlers = useRef({onPresented, onClose});
  handlers.current = {onPresented, onClose};
  const [reduced, setReduced] = useState(() => motion === false || matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const query = matchMedia('(prefers-reduced-motion: reduce)'), update = () => setReduced(motion === false || query.matches);
    update(); query.addEventListener('change', update); return () => query.removeEventListener('change', update);
  }, [motion]);
  useEffect(() => {
    const reveal = setTimeout(() => handlers.current.onPresented(notice.id), reduced ? 0 : 1800);
    const finish = setTimeout(() => handlers.current.onClose(notice.id), reduced ? 2200 : 4400);
    const escape = event => {if (event.key === 'Escape' && !event.defaultPrevented && !event.isComposing) {event.preventDefault(); handlers.current.onClose(notice.id);}};
    window.addEventListener('keydown', escape);
    const node = root.current;
    return () => {
      clearTimeout(reveal); clearTimeout(finish); window.removeEventListener('keydown', escape);
      if (node?.contains(document.activeElement) && !document.hidden && document.hasFocus() && focus.current?.isConnected) focus.current.focus({preventScroll: true});
    };
  }, [notice.id, reduced]);
  const from = notice.from === null ? '定级中' : TIER_NAMES[notice.from], to = TIER_NAMES[notice.to];
  return createPortal(<section ref={root} className="rank-promotion" data-rank-promotion data-reduced={reduced} role="status" aria-live="polite" aria-atomic="true" aria-label="段位晋升" style={{'--promotion-colour': COLOURS[notice.to]}}>
    <span className="sr-only">{from}晋升为{to}，能力分 {Math.round(notice.score)}。</span>
    <button type="button" className="promotion-skip" aria-label="跳过段位晋升动画" title="跳过 · Esc" onClick={() => onClose(notice.id)}><X size={20}/></button>
    <div className="promotion-stage" aria-hidden="true">
      <div className="promotion-heading">段位晋升</div>
      <div className="promotion-art">
        <div className="promotion-aura"/>
        <div className="promotion-orbit orbit-outer"/><div className="promotion-orbit orbit-inner"/>
        <div className="promotion-old">{notice.from !== null && <TierIcon badge={`tier-${notice.from}`} size={340}/>}<span>{from}</span></div>
        <div className="promotion-charge"/><div className="promotion-shockwave"/>
        <div className="promotion-sparks">{SPARKS.map((style, i) => <i key={i} style={style}/>)}</div>
        <div className="promotion-new">
          <div className="promotion-pieces">{['left', 'core', 'right'].map(piece => <div key={piece} className={`promotion-piece piece-${piece}`}><TierIcon badge={`tier-${notice.to}`} size={420}/></div>)}</div>
          <div className="promotion-complete"><TierIcon badge={`tier-${notice.to}`} size={420}/></div>
          <div className="promotion-sheen"/>
        </div>
      </div>
      <div className="promotion-result"><strong>{to}</strong><span className="promotion-rule"/><small>能力分 {Math.round(notice.score).toLocaleString('zh-CN')}</small></div>
    </div>
  </section>, document.body);
}
