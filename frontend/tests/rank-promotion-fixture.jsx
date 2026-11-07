import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import RankPromotion from '../src/components/RankPromotion.jsx';
import LevelUpDialog from '../src/components/LevelUpDialog.jsx';
import useRankPromotion from '../src/lib/useRankPromotion.js';
import useLevelUp from '../src/lib/useLevelUp.js';
import {emptyRankPromotion, rankPromotionKey} from '../src/lib/rankPromotions.js';
import '../src/styles/workspace.css';
import '../src/styles/polish.css';
const read = (key, fallback) => {try {return JSON.parse(localStorage.getItem('rank-fixture:' + key)) ?? fallback;} catch {return fallback;}};
const scores = [200, 850, 1000, 1150, 1300, 1450, 1650, 1850, 2050];
const make = (owner, index, revision, options = {}) => ({level: options.level ?? 11, confirmed: options.confirmed ?? true,
  authority: {owner: options.owner ?? owner, epoch: options.epoch ?? 'fixture-server', revision},
  ranked: {qualified: index !== null, abilityScore: options.score ?? scores[index] ?? 0, levelGate: 5}});
function Fixture() {
 const [owner, setOwner] = useState(() => read('owner', 'rank-owner'));
 const [growth, setGrowth] = useState(() => read('growth', make(owner, 1, 1)));
 const [blocked, setBlocked] = useState(() => read('blocked', false)), [other, setOther] = useState(false), [theme, setTheme] = useState('dark'), [motion, setMotion] = useState(true);
 const [prefs, setPrefs] = useState({levelNoticeVersion: 1, levelNoticeSeen: 11, levelNoticePending: 0});
 const rank = useRankPromotion({owner, growth, ready: true, blocked});
 const level = useLevelUp({owner, growth, preferences: prefs, preferencesReady: true, setPreferences: setPrefs, blocked: blocked || rank.pending || Boolean(rank.notice)});
 useEffect(() => {document.documentElement.dataset.theme = theme; document.documentElement.dataset.motion = motion ? 'on' : 'off';}, [theme, motion]);
 window.rankFixture = {
  emit: (index, revision, options = {}) => {const value = make(owner, index, revision, options); localStorage.setItem('rank-fixture:growth', JSON.stringify(value)); setGrowth(value);},
  block: value => {localStorage.setItem('rank-fixture:blocked', JSON.stringify(value)); setBlocked(value);},
  switchOwner: (value, index = 1) => {setOwner(value); localStorage.setItem('rank-fixture:owner', JSON.stringify(value)); const next = make(value, index, 1); setGrowth(next); localStorage.setItem('rank-fixture:growth', JSON.stringify(next)); setPrefs({levelNoticeVersion: 1, levelNoticeSeen: 11, levelNoticePending: 0});},
  reset: (from, to, id) => {const baseline = {...emptyRankPromotion(owner), initialized: true, rank: from}; localStorage.setItem(rankPromotionKey(owner), JSON.stringify(baseline)); localStorage.setItem('rank-fixture:growth', JSON.stringify(make(owner, to, id)));},
  other: setOther, theme: setTheme, motion: setMotion,
  snapshot: () => ({notice: rank.notice, pending: rank.pending, receipt: JSON.parse(localStorage.getItem(rankPromotionKey(owner)) || 'null'), level: level.dialog}),
 };
 return <main style={{padding: 24, maxWidth: 800}}><h1>段位晋升隔离验证</h1><label>练习草稿<textarea aria-label="练习草稿" defaultValue="// retained code" style={{display: 'block', width: '100%', height: 240}}/></label><button type="button">离开编辑器</button><p>{owner}</p>{other && <section role="dialog" aria-modal="true" aria-label="其它弹窗"><button onClick={() => setOther(false)}>关闭其它弹窗</button></section>}{rank.notice && <RankPromotion key={rank.notice.id} notice={rank.notice} motion={motion} onPresented={rank.presented} onClose={rank.close}/>} {level.dialog && <LevelUpDialog notice={level.dialog} pages={[]} preferences={prefs} onPresented={level.markPresented} onClose={level.close} onOpen={() => {}}/>}</main>;
}
createRoot(document.getElementById('root')).render(<React.StrictMode><Fixture/></React.StrictMode>);
