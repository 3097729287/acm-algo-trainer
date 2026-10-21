import PageSearch from '@/components/PageSearch.jsx';
import MedalEmblem, {titleMedalIndex} from '@/components/MedalEmblem.jsx';
import KnowledgeRadar from '@/components/KnowledgeRadar.jsx';
import FilterMenu from '@/components/FilterMenu.jsx';
import { CONTEST_SHELVES } from '@/components/ContestTabs.jsx';
import { CONTEST_KINDS, contestKind } from '@/lib/contestShelves.js';
import { ArrowDown, ArrowUp, FolderTree } from 'lucide-react';
import CatalogExplorer, { CatalogPath } from '../components/CatalogExplorer.jsx';
import Tooltip from '@/components/Tooltip.jsx';
import ProfileBadge from '@/components/ProfileBadge.jsx';
import { Info, Code2, Flame } from 'lucide-react';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import { useDeferredValue, useEffect, useMemo, useRef, useState } from 'react';
import InlineTitle from '@/components/InlineTitle.jsx';
import TitleMedals from '../components/TitleMedals.jsx';
import { ArrowLeft, ArrowRight, Award, BookOpen, CalendarDays, Check, CheckCheck, Circle, ChevronRight, ExternalLink, Flag, Github, LoaderCircle, Play, RefreshCw, Search, Target, TrendingUp, Trophy, UserRound } from 'lucide-react';
import { compareContestNewest, contestTime, difficultyBand, difficultyLabel, difficultyDescription } from '@/lib/practiceMetadata.js';
import './ProgressPanels.css';
import GoalsPanel from './GoalsPanel.jsx';
import TierIcon from '@/components/TierIcon.jsx';
import ContestTabs, { isXcpc, matchesShelf } from '@/components/ContestTabs.jsx';
import { knowledgeLabels } from '@/lib/knowledgeLabels.js';
import { ProfileSettings } from './CommunityPanel.jsx';
import { MiniLeaderboard } from '../components/WorkspaceDecorations.jsx';

const PLATFORMS = [
  ['codeforces', 'Codeforces', 'Handle'], ['atcoder', 'AtCoder', '用户名'],
];
const LABELS = Object.fromEntries(PLATFORMS.map(([key, name]) => [key, name]));
const ACCOUNT_FIELDS=[...PLATFORMS,['nowcoder','牛客','用户 ID'],['luogu','洛谷','用户 ID']];
const number = value => typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('zh-CN') : '—';
const list = value => Array.isArray(value) ? value : [];
// Display copy stays compatible with the descriptions returned by existing installations.
const acText = value => String(value || '').replace(/官方首次\s*AC/g, '首次 AC').replace(/官方\s*AC/g, ' AC').replace(/\s+/g, ' ').trim();
const achievementText = value => acText(value).replace(/[；;]\s*(?:样例通过|看题解后的\s*AC)\s*不计入[。. ]*/g, '').replace('通过来自两个平台的本地审核题目', 'AC 来自两个平台的题目');
const confidence = value => ({ none: '证据不足', low: '证据较少', medium: '中等可信', high: '证据充分' }[value] || '证据不足');
const STAGES = { foundation: '基础起步', consolidate: '巩固练习', stretch: '逐步挑战', retry: '复习与补题' };
const PROJECT_URL = 'https://github.com/3097729287/acm-algo-trainer';
const contestDateLabel = row => {
  const time = contestTime(row);
  const year = row.eventYear || row.examYear || row.xcpcYear || row.rows?.[0]?.eventYear || row.rows?.[0]?.xcpcYear;
  return time == null ? (year ? `${year} 年 · 日期待核实` : '日期待同步') : new Date(time).toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' });
};
const dateLabel = value => {
  if (!value) return '尚未更新';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};
const clamp = (value, max = 100) => Math.max(0, Math.min(max, Number(value) || 0));
function Loading({ text = '正在读取记录' }) { return <div className="progress-empty" role="status"><LoaderCircle size={21} className="progress-spin" /><span>{text}</span></div>; }
function Empty({ children }) { return <div className="progress-empty">{children}</div>; }
function Meter({ value, label }) { return <span className="progress-meter" role="meter" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={clamp(value)}><i style={{ width: `${clamp(value)}%` }} /></span>; }

export { default as TitleMedals } from '../components/TitleMedals.jsx';

export function AchievementPanel({ achievements = [], newIds = [], onSeen }) {
  const [filter, setFilter] = useState('all');
  const [seen, setSeen] = useState(() => new Set());
  const fresh = new Set(newIds);
  const markSeen = id => {
    if (seen.has(id) || !fresh.has(id)) return;
    setSeen(previous => new Set([...previous, id]));
    onSeen?.(id);
  };
  const items = list(achievements).map(item => ({ ...item, name: acText(item.name), description: achievementText(item.description) })).filter(item => filter === 'all' || (filter === 'unlocked' ? item.unlocked : !item.unlocked)).slice().sort((left, right) => Number(right.unlocked) - Number(left.unlocked));
  return <div className="achievement-panel"><div className="ranking-tabs" role="group" aria-label="成就筛选">{[['all', '全部成就'], ['unlocked', '已达成'], ['pending', '待达成']].map(([value, label]) => <button className={filter === value ? 'active' : ''} aria-pressed={filter === value} key={value} onClick={() => setFilter(value)}>{label}</button>)}</div><div className="progress-achievements">{items.map(item => {
    const isNew = item.unlocked && fresh.has(item.id) && !seen.has(item.id);
    return <div className={`progress-achievement${item.unlocked ? ' progress-unlocked' : ''}${isNew ? ' progress-achievement-new' : ''}`} key={item.id} data-achievement-id={item.id} tabIndex={isNew ? 0 : undefined} onMouseEnter={() => markSeen(item.id)} onFocus={() => markSeen(item.id)}><MedalEmblem size={36} variant={item.rewardTitle?.category==='streak'?'streak':'ac'} index={item.rewardTitle?titleMedalIndex(item.rewardTitle):Math.min(9,Math.floor(Math.log2(item.target||1)))}/><div><div className="progress-achievement-name"><strong>{item.name}</strong>{isNew && <span className="achievement-new-label">新达成</span>}</div><p>{item.description}</p>{!item.unlocked && <Meter value={item.target ? item.progress / item.target * 100 : 0} label={`${item.name}完成进度`} />}<div className="progress-achievement-status"><span>{item.unlocked ? `已达成${item.unlockedAt ? ' · ' + dateLabel(item.unlockedAt) : ''}` : `${number(item.progress)} / ${number(item.target)}`}</span>{item.rewardTitle ? <span className={`achievement-title-reward${item.unlocked ? ' claimed' : ''}`}><Award size={14} aria-hidden="true" />{item.rewardTitle.name} · {item.unlocked ? '称号已获得' : '达成后获得称号'}</span> : item.rewardXp > 0 && <span className={`achievement-reward${item.rewardClaimed ? ' claimed' : ''}`}>+{number(item.rewardXp)} XP · {item.rewardClaimed ? '已发放' : item.unlocked ? '待发放' : '达成后发放'}</span>}</div></div></div>;
  })}</div>{!items.length && <p className="progress-muted">这一组暂时没有成就记录。</p>}</div>;
}
export function DailyTasks({ dailyTasks, goalTasks, onTrain, onClaim }) {
  const [claiming, setClaiming] = useState(null), [error, setError] = useState('');
  const tasks = list(dailyTasks?.tasks);
  async function claim(task) { if (claiming || !task.completed || task.claimed) return; setClaiming(task.id); setError(''); try { await onClaim?.(task.id, dailyTasks.date); } catch (issue) { setError(issue.message); } finally { setClaiming(null); } }
  const targets=list(goalTasks || dailyTasks?.goalTasks);
  return <section className="progress-section daily-tasks" aria-label="每日任务"><div className="progress-section-heading"><h2><CalendarDays size={18} />每日任务</h2><span>{dailyTasks?.date || '每日更新'} · {tasks.filter(task => task.claimed).length}/{tasks.length}</span></div><p className="progress-small">按北京时间刷新，同题当天只计一次原站 AC。</p><div className="daily-task-grid">{tasks.map(task => <article className={`daily-task${task.claimed ? ' daily-task-claimed' : ''}`} key={task.id}><div className="daily-task-main"><div><strong>{task.title}</strong><span className="daily-task-xp">+{number(task.xp)} XP</span></div><p>{acText(task.description)}</p><div className="daily-task-progress"><Meter value={task.target ? task.progress / task.target * 100 : 0} label={`${task.title}任务进度`} /><span>{number(task.progress)}/{number(task.target)}</span></div></div><button className={'progress-button ' + (task.completed && !task.claimed ? 'progress-primary' : '')} disabled={!task.completed || task.claimed || !!claiming || !onClaim} onClick={() => claim(task)}>{claiming === task.id ? <LoaderCircle size={13} className="spin" /> : task.claimed ? <Check size={13} /> : null}{task.claimed ? '已领取' : task.completed ? '领取经验' : '进行中'}</button></article>)}</div>{targets.length>0&&<section className="daily-goal-tasks" aria-label="目标题目"><div className="daily-goal-heading"><h3><Target size={17}/>目标题目</h3><span>{targets.filter(task=>task.accepted).length}/{targets.length} 已 AC</span></div>{targets.map(task=><button className="daily-goal-row" data-accepted={task.accepted} key={task.id} onClick={()=>onTrain?.(task.id)}><span className="daily-goal-state">{task.accepted ? <Check size={16}/> : <Circle size={14}/>}</span><div><strong><InlineTitle>{task.title}</InlineTitle></strong><small>{task.contest}{task.problem?` · ${task.problem}`:''} · {(task.goalTitles || []).join('、')}</small></div><span>{task.accepted?'AC':difficultyLabel(task).replace(/^≈\s*/, '')}</span><ChevronRight size={15}/></button>)}</section>}{!tasks.length && <p className="progress-muted">每日任务正在准备。</p>}{error && <p role="alert" className="connection-error">{error}</p>}</section>;
}

export function GrowthAccountPanel({ api, hub, account, profile, profileSnapshot: suppliedSnapshot, onProfileChanged, onHubChanged, onError, accountFocus }) {
  const panelRef = useRef(null);
  const profileSnapshot = useMemo(() => suppliedSnapshot || (profile ? { profile } : undefined), [profile, suppliedSnapshot]);
  const [publicOpen, setPublicOpen] = useState(false);
  const focusSection = typeof accountFocus === 'string' ? accountFocus : accountFocus?.section;
  useEffect(() => {
    if (!focusSection) return;
    if (focusSection === 'connections' || focusSection === 'public') setPublicOpen(true);
    const frame = requestAnimationFrame(() => {
      const target = panelRef.current;
      target?.scrollIntoView({ block: 'start' });
    });
    return () => cancelAnimationFrame(frame);
  }, [accountFocus, focusSection]);
  return <section ref={panelRef} id="growth-accounts" className="progress-section growth-account-panel" aria-label="账号与身份">
    <ProfileSettings api={api} initialAccount={account} initialProfileSnapshot={profileSnapshot} onChanged={onProfileChanged} onError={onError} />
    <details className="growth-account-section" open={publicOpen} onToggle={event => setPublicOpen(event.currentTarget.open)}><summary><UserRound size={16} />公开账号与评分<ChevronRight size={15} /></summary>{publicOpen && <ConnectionsPanel hub={hub} api={api} onChanged={onHubChanged} onError={onError} includeTranslation={false} />}</details>
  </section>;
}

export function GrowthPage({avatarData,onAvatar,goalOverview,api,onGoalsChanged,insights,account,profile,onTopic,onTrain,onAccounts,onAchievements}) {
 if(!insights)return <Loading/>;
 const summary=insights.summary||{},growth=insights.growth||{},rank=growth.ranked||{},nickname=profile?.nickname||account?.nickname||insights.profile?.nickname||'练习者';
 const stats=[[Check,summary.totalSolved??summary.officialSolved,'总 AC'],[Code2,summary.submissions,'提交'],[CalendarDays,summary.activeDays,'活跃天数'],[Flame,summary.streak,'连续练习'],[Flag,summary.completedContests,'完成比赛']];
 const rankName=Number(growth.level)<5?'未定级':rank.qualified===false?'定级中':rank.tier||'定级中';
 return <div className="progress-page growth-dashboard" aria-label="成长与能力"><div className="progress-growth-columns">
 <KnowledgeRadar knowledge={insights.knowledge||[]} onTopic={onTopic} onTrain={onTrain}/>
 <section className="progress-section growth-account-hero" aria-label="账号成长统计"><div className="account-hero-identity"><ProfileBadge compact={false} growth={growth} avatar={avatarData} nickname={nickname} onAvatarClick={onAvatar} onClick={onAccounts}/><div className="account-hero-rank"><TierIcon badge={rank.badge||'tier-0'} size={180}/><strong>{rankName}</strong>{rank.abilityScore!=null&&<span>{number(rank.abilityScore)}</span>}</div></div>
 <div className="account-hero-level"><span>Lv.{growth.level??'—'}</span><div><Meter value={growth.nextLevelXp?Number(growth.currentLevelXp||0)/growth.nextLevelXp*100:0} label="等级经验"/><span>{number(growth.currentLevelXp||0)} / {number(growth.nextLevelXp||0)} XP</span></div></div>
 <div className="account-hero-statistics">{stats.map(([Icon,value,label])=><div key={label}><Icon size={21}/><b>{number(value)}</b><span>{label}</span></div>)}</div><div className="account-hero-titles"><TitleMedals titles={insights.equippedTitles||growth.equippedTitles||[]}/></div><button type="button" className="text-button" onClick={onAchievements}><Award size={18}/>成就与称号</button>
 </section></div><section id="growth-goals" className="progress-section">{api&&<GoalsPanel api={api} overview={goalOverview} onChanged={onGoalsChanged}/>}</section></div>;
}

const dayKey = date => date.toISOString().slice(0, 10);
const activityLevel = amount => amount <= 0 ? 0 : amount === 1 ? 1 : amount <= 3 ? 2 : amount <= 6 ? 3 : 4;
function PassCount({ count = 0 }) {
  return <span className={`activity-pass-count activity-pass-${activityLevel(count)}`} aria-label={`${number(count)} 题通过`}><b>{number(count)}</b><span>题</span><i aria-hidden="true"><em style={{ width: `${Math.min(100, count / 7 * 100)}%` }} /></i></span>;
}
export function ActivityPage({ insights, onTrain }) {
  const todayKey = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
  const currentYear = Number(todayKey.slice(0, 4));
  const [year, setYear] = useState(currentYear);
  const [selected, setSelected] = useState(todayKey);
  const [focused, setFocused] = useState(todayKey);
  const focusRef = useRef(todayKey), buttons = useRef(new Map());
  const activity = useMemo(() => new Map(list(insights?.activity).map(item => [item.date, item])), [insights?.activity]);
  const days = useMemo(() => {
    const result = [], begin = new Date(Date.UTC(year, 0, 1)), stop = new Date(Date.UTC(year + 1, 0, 1));
    for (let date = begin; date < stop && dayKey(date) <= todayKey; date = new Date(+date + 86400000)) result.push(dayKey(date));
    return result;
  }, [year, todayKey]);
  const years = [...new Set([currentYear, ...list(insights?.activity).map(item => Number(String(item.date).slice(0, 4))).filter(value => Number.isFinite(value) && value <= currentYear)])].sort((a, b) => b - a).slice(0, 6);
  const offset = (new Date(Date.UTC(year, 0, 1)).getUTCDay() + 6) % 7;
  useEffect(() => {
    const next = days.includes(selected) ? selected : days[days.length - 1];
    setSelected(next); setFocused(next); focusRef.current = next;
  }, [year, days]);
  if (!insights) return <Loading />;
  const selectedData = activity.get(selected) || { date: selected, submissions: 0, accepted: 0, officialAccepted: 0 };
  const focusedData = activity.get(focused) || { submissions: 0, accepted: 0, officialAccepted: 0 };
  const selectedDays = days.filter(key => activity.has(key));
  const totals = days.reduce((value, key) => {
    const passed = activity.get(key)?.officialAccepted || 0;
    value.official += passed;
    value.current = passed > 0 ? value.current + 1 : 0;
    value.longest = Math.max(value.longest, value.current);
    return value;
  }, { official: 0, current: 0, longest: 0 });
  const focusDay = key => { focusRef.current = key; setFocused(key); buttons.current.get(key)?.focus(); };
  const handleKey = event => {
    const index = days.indexOf(focusRef.current);
    let next;
    if (event.key === 'ArrowLeft') next = index - 7;
    else if (event.key === 'ArrowRight') next = index + 7;
    else if (event.key === 'ArrowUp') next = index - 1;
    else if (event.key === 'ArrowDown') next = index + 1;
    else if (event.key === 'Home') next = event.ctrlKey ? 0 : index - ((index + offset) % 7);
    else if (event.key === 'End') next = event.ctrlKey ? days.length - 1 : index + 6 - ((index + offset) % 7);
    if (next != null) { event.preventDefault(); event.stopPropagation(); focusDay(days[clamp(next, days.length - 1)]); }
  };
  return <div className="activity-page" aria-label="训练活动">
    <section className="progress-section"><div className="progress-section-heading"><h2><CalendarDays size={17} /><Tooltip label="训练日历说明" text="按北京时间统计原站 AC，同题同日计一次；颜色依次对应 0、1、2–3、4–6、7+ 题。方向键移动，Enter 查看当天。"/></h2><label className="activity-year">年份<ThemedSelect aria-label="活动年份" value={year} onChange={event => setYear(Number(event.target.value))}>{years.map(value => <option key={value}>{value}</option>)}</ThemedSelect></label></div>
      <div className="progress-stat-line activity-stats"><span className="activity-year-total"><b>{number(totals.official)}</b><span>题次通过</span></span><span className="activity-year-streak"><b>{number(totals.longest)}</b><span>天最长连续通过</span></span></div>
      <div className="activity-calendar-scroll"><div className="activity-calendar" role="grid" aria-label={`${year}年训练热力图，方向键移动，Enter查看日期`} onKeyDown={handleKey}>
        {Array.from({ length: offset }, (_, index) => <span className="activity-day activity-padding" role="presentation" key={'pad' + index} />)}
        {days.map(key => {
          const amount = activity.get(key)?.officialAccepted || 0;
          const level = activityLevel(amount);
          const description = `${key}，${amount} 题通过`;
          return <button type="button" role="gridcell" className={`activity-day activity-level-${level}${selected === key ? ' activity-selected' : ''}`} key={key} ref={node => { if (node) buttons.current.set(key, node); else buttons.current.delete(key); }}
            tabIndex={focused === key ? 0 : -1} aria-label={description} aria-selected={selected === key} title={description} onFocus={() => { focusRef.current = key; setFocused(key); }} onClick={() => { focusRef.current = key; setFocused(key); setSelected(key); }} />;
        })}
      </div></div>
      <div className="activity-calendar-caption"><Tooltip text="0 / 1 / 2–3 / 4–6 / 7+ 题"><span className="activity-legend" tabIndex={0} aria-label="热力图图例">{[0,1,2,3,4].map(level=><i key={level} className={`activity-level-${level}`}/>)}</span></Tooltip></div>
    </section>
    <section className="progress-section activity-day-detail"><div className="progress-section-heading"><h2>{selected || '日期详情'}</h2></div>
    <PassCount count={selectedData.officialAccepted || 0} /></section>
    <section className="progress-section"><details className="activity-details" open><summary>查看日期明细（{selectedDays.length} 天）</summary>{selectedDays.length ? <div className="progress-table-scroll"><table><thead><tr><th>日期</th><th>通过题数</th></tr></thead><tbody>{selectedDays.slice().reverse().map(key => { const item = activity.get(key); return <tr key={key}><td><button type="button" className="progress-text-button" onClick={() => { setSelected(key); focusDay(key); }}>{key}</button></td><td><PassCount count={item.officialAccepted || 0} /></td></tr>; })}</tbody></table></div> : <p className="progress-muted">这一年还没有记录。完成正式提交后会自动记录。</p>}</details>
      {insights.recommendations?.[0]?.ids?.[0] && onTrain && <button type="button" className="progress-button" onClick={() => onTrain(insights.recommendations[0].ids[0])}>继续练习<ArrowRight size={13} /></button>}
    </section>
  </div>;
}

function contestGroups(rows) {
  const map = new Map();
  for (const row of list(rows)) {
    const key = `${row.platform || ''}::${row.contest}`;
    if (!map.has(key)) map.set(key, { key, name: row.contest, platform: row.platform, series: row.series, examYear: row.examYear ?? row.xcpcYear, examStage: row.examStage ?? row.xcpcKind, xcpc: isXcpc(row), notice: row.collectionNotice, rows: [] });
    map.get(key).rows.push(row);
  }
  return [...map.values()].map(group => ({ ...group, rows: group.rows.sort((a, b) => String(a.problem).localeCompare(String(b.problem), 'en', { numeric: true })) })).sort(compareContestNewest);
}
function Difficulty({ row, locked = false }) { return <span className={`competition-difficulty competition-difficulty-${locked ? 'unknown' : difficultyBand(row.difficulty)}${locked ? ' competition-hidden-difficulty' : ''}`} title={locked ? '比赛进行中，赛后显示难度' : difficultyDescription(row)}>{locked ? '赛中隐藏' : difficultyLabel(row).replace(/^≈\s*/, '')}</span>; }
function ContestGrade({ group, locked = false }) {
  if (locked) return null;
  const gym = group.rows.find(row => Number.isInteger(row.contestDifficulty) && row.contestDifficulty >= 1 && row.contestDifficulty <= 5);
  if (gym) return <span className="contest-grade" title={gym.contestDifficultySource}>整场 {gym.contestDifficulty}/5 · {['基础', '进阶', '较难', '困难', '高难'][gym.contestDifficulty - 1]}</span>;
  const ratings = group.rows.map(row => row.difficulty).filter(value => typeof value === 'number').sort((a, b) => a - b);
  if (ratings.length < group.rows.length / 2) return <span className="contest-grade">已定级 {ratings.length}/{group.rows.length} 题</span>;
  const median = ratings[Math.floor(ratings.length / 2)];
  return <span className="contest-grade" title={`已评级 ${ratings.length}/${group.rows.length} 题的难度中位数，仅供训练参考`}>参考 ≈{median}</span>;
}
export function CompetitionPage({ rows, workspace, hub, onTrain, onJoin, onStartReproduction, initialContest, onBack }) {
  const groups = useMemo(() => contestGroups(list(rows).filter(row => !row.catalogHidden)), [rows]);
  const [query, setQuery] = useState(''), [filter, setFilter] = useState('all');
  const deferredQuery = useDeferredValue(query);
  const [shelf, setShelf] = useState('all'), [examYear, setExamYear] = useState(''), [examStage, setExamStage] = useState('');
  const [folder,setFolder]=useState(null), [kind,setKind]=useState(''), [descending,setDescending]=useState(true);
  const [sort, setSort] = useState('newest');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(null), [joining, setJoining] = useState(false), [joinError, setJoinError] = useState(''), [starting, setStarting] = useState(null);
  const progress = useMemo(() => new Map(list(workspace?.training).map(row => [row.id, row])), [workspace?.training]);
  const lockedIds = useMemo(() => new Set(workspace?.activeContest?.status === 'running' ? list(workspace.activeContest.slots).map(row => row.id) : []), [workspace?.activeContest]);
  const counts = useMemo(() => new Map(groups.map(group => [group.key, {
    active: group.rows.filter(row => progress.has(row.id)).length,
    accepted: group.rows.filter(row => progress.get(row.id)?.accepted).length,
  }])), [groups, progress]);
  const activeCount = group => counts.get(group.key)?.active || 0;
  const acceptedCount = group => counts.get(group.key)?.accepted || 0;
  const filtered = useMemo(() => {
    const search = deferredQuery.trim().toLowerCase();
    return groups.filter(group => matchesShelf(group, shelf)
      && (!kind || contestKind(group)===kind) && (!examYear || String(group.examYear) === examYear) && (!examStage || group.examStage === examStage)
      && (!search || `${group.name} ${group.platform} ${group.rows.map(row => `${row.title} ${row.problem} ${lockedIds.has(row.id) ? '' : list(row.tags).join(' ')}`).join(' ')}`.toLowerCase().includes(search))
      && (filter === 'all' || filter === 'joined' ? filter === 'all' || counts.get(group.key).active > 0 : filter === 'available' ? counts.get(group.key).active === 0 : counts.get(group.key).accepted < group.rows.length))
      .sort((a,b) => (sort === 'name' ? a.name.localeCompare(b.name, 'zh-CN', {numeric:true}) : -compareContestNewest(a,b)) * (descending ? -1 : 1));
  }, [groups, shelf, examYear, examStage, deferredQuery, lockedIds, filter, counts, sort, kind, descending]);
  useEffect(() => { setPage(1); }, [deferredQuery, shelf, examYear, examStage, filter, sort, kind, descending]);
  const pageSize = 40, pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pageCount), first = (currentPage - 1) * pageSize;
  const visibleGroups = filtered.slice(first, first + pageSize);
  useEffect(() => {
    if (!initialContest) return;
    const name = typeof initialContest === 'string' ? initialContest : initialContest.name || initialContest.contest || initialContest.id;
    const group = groups.find(item => item.key === name || item.name === name);
    if (group) setSelected(group.key);
  }, [initialContest, groups]);
  if (!rows) return <Loading text="正在读取比赛列表" />;
  const current = groups.find(group => group.key === selected);
  const join = async group => { if (!onJoin || joining) return; setJoining(true); setJoinError(''); try { await onJoin(group.name); } catch (issue) { setJoinError(issue.message || '暂时无法加入训练，请重试。'); } finally { setJoining(false); } };
  const start = async group => { if (!onStartReproduction || starting) return; setStarting(group.key); setJoinError(''); try { await onStartReproduction(group.name); } catch (issue) { setJoinError(issue.message || '暂时无法开始比赛，请重试。'); } finally { setStarting(null); } };
  const startButton = group => onStartReproduction && <button type="button" className="progress-button progress-primary competition-start" disabled={!!starting} onClick={() => start(group)} aria-label={`开始比赛 ${group.name}`}>{starting === group.key ? <LoaderCircle size={14} className="progress-spin" /> : <Play size={14} />}{starting === group.key ? '正在开始' : '开始比赛'}</button>;
  if (current) {
    const inMock = current.rows.some(row => lockedIds.has(row.id));
    return <div className="competition-page competition-detail" aria-label={`${current.name}比赛详情`}>
      <div className="competition-detail-heading"><button type="button" className="progress-button" onClick={() => { setSelected(null); if (initialContest) onBack?.(); }}><ArrowLeft size={14} />全部比赛</button><div><h2>{current.name}</h2><span>{current.platform} · {contestDateLabel(current)} · {current.rows.length} 题 · 已通过 {acceptedCount(current)} 题 <ContestGrade group={current} locked={inMock} /></span></div>{onJoin && <button type="button" className="progress-button" disabled={joining || inMock || activeCount(current) === current.rows.length} onClick={() => join(current)}>{joining ? <LoaderCircle size={14} className="progress-spin" /> : <Flag size={14} />}{activeCount(current) === current.rows.length ? '已加入训练' : activeCount(current) ? '加入剩余题目' : '加入我的训练'}</button>}{startButton(current)}</div>
      {inMock && <div className="competition-notice">本场部分题目正在模拟赛中，难度和知识点将在赛后显示。请从模拟赛页继续。</div>}
      {current.notice && <div className="competition-notice">{current.notice}题面可直接练习，题解逐步补充。</div>}
      {joinError && <p className="connection-error" role="alert">{joinError}</p>}
      <div className="competition-question-list">{current.rows.map(row => {
        const state = progress.get(row.id), locked = lockedIds.has(row.id);
        return <button type="button" className="competition-question" key={row.id} disabled={!onTrain || locked} onClick={() => onTrain?.(row.id)} aria-label={`练习 ${row.problem} ${row.title}`}><span className="competition-letter">{row.problem}</span><div className="competition-question-main"><strong><InlineTitle>{row.title}</InlineTitle></strong><div className="competition-question-meta">{locked ? <span>模拟赛进行中</span> : knowledgeLabels(row).map(tag => <span className="competition-tag" key={tag}>{tag}</span>)}<span>{row.solutionAvailable === false ? '题解未生成' : row.solutionAvailable === true ? '有题解' : '题解状态未知'}</span></div></div><Difficulty row={row} locked={locked} /><span className={`competition-result${state?.accepted ? ' competition-accepted' : ''}`}>{locked ? '考场中' : state?.accepted ? (state.scope === 'official' ? '官方通过' : '本地通过') : state?.verdict === 'SAMPLE_PASS' ? '样例通过' : state ? '已加入' : '未加入'}</span><ChevronRight size={15} aria-hidden="true" /></button>;
      })}</div>
    </div>;
  }
  const renderCard = group => <article className="competition-card" key={group.key}><button type="button" className="competition-card-open" onClick={() => setSelected(group.key)} aria-label={`查看 ${group.platform} ${group.name}，${group.rows.length} 道题`}><span className="competition-card-title"><strong>{group.name}</strong></span><span className="competition-problem-tokens">{group.rows.map(row => <span className={`competition-problem-token${progress.get(row.id)?.accepted ? ' competition-token-accepted' : ''}`} key={row.id}><b>{row.problem}{typeof row.difficulty==='number' && !lockedIds.has(row.id) ? ':' : ''}</b>{typeof row.difficulty==='number' && !lockedIds.has(row.id) && <Difficulty row={row}/>}</span>)}</span><ChevronRight size={16}/></button>{startButton(group)}</article>;
  const reset = () => {setShelf('all');setKind('');setExamYear('');setExamStage('');setFilter('all');};
  return <div className="competition-page" aria-label="比赛列表">
    <PageSearch><label className="search-box"><Search size={17}/><input value={query} onChange={event=>setQuery(event.target.value)} aria-label="搜索比赛"/></label>
    <FilterMenu label="筛选比赛" active={shelf!=='all'||!!kind||!!examYear||filter!=='all'} onReset={reset}>
      <details className="filter-submenu" open><summary>比赛分类</summary><div className="filter-choice-grid">{CONTEST_SHELVES.map(([id,label])=><button type="button" key={id} aria-pressed={shelf===id} onClick={()=>{setShelf(id);setFolder(null);setExamYear('');setExamStage('');}}>{label}</button>)}</div><div className="filter-choice-grid">{CONTEST_KINDS.map(([id,label])=><button type="button" key={id} aria-pressed={kind===id} onClick={()=>{setKind(kind===id?'':id);setFolder(null);}}>{label}</button>)}</div></details>
      <label className="filter-field"><span>年份</span><ThemedSelect aria-label="比赛年份" value={examYear} onChange={event=>setExamYear(event.target.value)}><option value="">全部年份</option>{[...new Set(groups.map(group=>group.examYear).filter(Boolean))].sort((a,b)=>b-a).map(year=><option key={year}>{year}</option>)}</ThemedSelect></label>
      <label className="filter-field"><span>训练情况</span><ThemedSelect value={filter} onChange={event=>setFilter(event.target.value)} aria-label="比赛训练情况"><option value="all">全部比赛</option><option value="joined">已加入训练</option><option value="available">尚未加入</option><option value="unfinished">尚未全部通过</option></ThemedSelect></label>
      <label className="filter-field"><span>排序</span><ThemedSelect aria-label="比赛排序" value={sort} onChange={event=>setSort(event.target.value)}><option value="newest">比赛时间</option><option value="name">名称</option></ThemedSelect></label>
      <label className="filter-field"><span>方向</span><ThemedSelect aria-label="比赛排序方向" value={descending?'desc':'asc'} onChange={event=>setDescending(event.target.value==='desc')}><option value="desc">倒序</option><option value="asc">正序</option></ThemedSelect></label>
      <label className="filter-field"><span>文件夹浏览</span><input type="checkbox" aria-label="比赛文件夹浏览" checked={!!folder} onChange={event=>setFolder(event.target.checked?{stage:'platforms',path:[]}:null)}/></label>
      <span className="filter-result-count">{filtered.length} 场</span>
    </FilterMenu></PageSearch>
    {joinError&&<p className="connection-error" role="alert">{joinError}</p>}
    {folder?<><CatalogPath scope={folder} onChange={setFolder}/><CatalogExplorer rows={filtered.flatMap(group=>group.rows.map(row=>({...row,groupKey:group.key})))} scope={folder} onChange={setFolder} onContest={row=>setSelected(row.groupKey)} renderContest={row=>renderCard(groups.find(group=>group.key===row.groupKey))}/></>:<div className="competition-list">{visibleGroups.map(renderCard)}</div>}
    {!folder&&filtered.length>pageSize&&<nav className="competition-pagination" aria-label="比赛分页"><span>{first+1}–{Math.min(first+pageSize,filtered.length)} / {filtered.length} 场</span><button type="button" className="progress-button" disabled={currentPage===1} onClick={()=>setPage(currentPage-1)}>上一页</button><span>第 {currentPage} / {pageCount} 页</span><button type="button" className="progress-button" disabled={currentPage===pageCount} onClick={()=>setPage(currentPage+1)}>下一页</button></nav>}
    {!filtered.length&&<Empty><Flag size={24}/><span>没有匹配的比赛</span></Empty>}
  </div>;
}

function accountDraft(hub) { return Object.fromEntries(ACCOUNT_FIELDS.map(([key]) => [key, hub?.settings?.accounts?.[key] || ''])); }
export function TranslationSettings({ api, onError }) {
  const apiRef = useRef(api), saving = useRef(false);
  apiRef.current = api;
  const [settings, setSettings] = useState(null), [draft, setDraft] = useState({ provider: 'deepseek', model: '', baseUrl: '' });
  const [apiKey, setApiKey] = useState(''), [loading, setLoading] = useState(true), [busy, setBusy] = useState(false);
  const [error, setError] = useState(''), [message, setMessage] = useState(''), [loadAttempt, setLoadAttempt] = useState(0);
  useEffect(() => {
    let alive = true;
    setLoading(true); setError('');
    if (!apiRef.current) { setLoading(false); return; }
    apiRef.current('translation/settings').then(answer => {
      if (!alive) return;
      setSettings(answer); setDraft({ provider: answer.provider, model: answer.model || '', baseUrl: answer.baseUrl || '' });
    }).catch(issue => { if (alive) setError(issue.message || '暂时无法读取翻译配置。'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [loadAttempt]);
  const save = async clearKey => {
    if (!apiRef.current || !settings || saving.current) return;
    saving.current = true; setBusy(true); setError(''); setMessage('');
    const body = { provider: draft.provider, model: draft.model.trim(), ...(draft.provider === 'custom' ? { baseUrl: draft.baseUrl.trim() } : {}), ...(clearKey ? { apiKey: '' } : apiKey.trim() ? { apiKey: apiKey.trim() } : {}) };
    try {
      const answer = await apiRef.current('translation/settings', body);
      setSettings(answer); setDraft({ provider: answer.provider, model: answer.model || '', baseUrl: answer.baseUrl || '' }); setApiKey('');
      setMessage(clearKey ? '已清除本机保存的密钥；已有环境配置仍可能继续生效。' : '翻译配置已保存，首次翻译时验证连接。');
    } catch (issue) { setError(issue.message || '未能保存翻译配置。'); onError?.(issue.message || '未能保存翻译配置'); }
    finally { saving.current = false; setBusy(false); }
  };
  const providers = list(settings?.providers).some(item => item.id === 'custom') ? list(settings.providers) : [...list(settings?.providers), { id: 'custom', name: '自定义 API', defaultModel: '' }], disabled = loading || busy || !settings;
    async function testConnection() {
    if (busy) return;setBusy(true);setError('');setMessage('');
    try { const result=await api('translation/test',{});setSettings(result);setMessage(result.message || '连接成功'); }
    catch(issue) { setError(issue.message);onError?.(issue.message); }
    finally { setBusy(false); }
  }
  return <div className="translation-settings" aria-label="题面翻译配置"><div className="progress-section-heading"><h3>题面翻译</h3><span>{loading ? '读取配置…' : settings?.verified ? '连接已验证' : settings?.configured ? '已配置 · 尚待实际翻译验证' : '尚未配置'}</span></div>
    <p className="progress-small">只翻译公开题面。在练习页点击“中文”，失败时保留原文。</p>
    <form onSubmit={event => { event.preventDefault(); save(false); }}><div className="translation-fields">
      <label><span>服务</span><ThemedSelect aria-label="翻译服务" value={draft.provider} disabled={disabled} onChange={event => { const provider = providers.find(item => item.id === event.target.value); setDraft({ provider: event.target.value, model: provider?.defaultModel || '', baseUrl: '' }); setApiKey(''); setMessage(''); }}>{providers.length ? providers.map(item => <option key={item.id} value={item.id}>{item.name}</option>) : <option value="deepseek">DeepSeek</option>}</ThemedSelect></label>
      <label><span>模型 / 接入点 ID</span><input aria-label="翻译模型" value={draft.model} disabled={disabled} required={['huoshan', 'custom'].includes(draft.provider)} maxLength={128} autoComplete="off" spellCheck={false} onChange={event => setDraft(previous => ({ ...previous, model: event.target.value }))} /></label>
      {draft.provider === 'custom' && <label className="translation-base-field"><span>Base URL</span><input type="url" aria-label="翻译 API Base URL" value={draft.baseUrl} disabled={disabled} required placeholder="https://api.example.com/v1" autoComplete="off" spellCheck={false} onChange={event => setDraft(previous => ({ ...previous, baseUrl: event.target.value }))} /></label>}
      <label className="translation-key-field"><span>API Key（可选）</span><input type="password" aria-label="翻译服务 API Key" value={apiKey} disabled={disabled} autoComplete="off" spellCheck={false} placeholder="留空保留当前密钥" onChange={event => setApiKey(event.target.value)} /></label>
    </div><p className="progress-small">{draft.provider === 'custom' ? '支持兼容 OpenAI 的接口。填写 Base URL、模型与 API Key；本地网关可不填密钥。' : '密钥不回显；更换服务时使用对应服务的密钥。'}</p><div className="progress-actions"><button type="submit" className="progress-button" disabled={disabled}>{busy ? <LoaderCircle size={14} className="progress-spin" /> : <Check size={14} />}保存翻译配置</button><button type="button" className="progress-button" disabled={disabled || !settings?.configured} onClick={testConnection}><RefreshCw size={14} />测试连接</button>{settings?.keyStored && draft.provider === settings.provider && <button type="button" className="progress-text-button" disabled={disabled} onClick={() => save(true)}>清除本机密钥</button>}{!settings && !loading && <button type="button" className="progress-text-button" onClick={() => setLoadAttempt(value => value + 1)}>重新读取</button>}</div></form>
    {settings?.notice && <p className="progress-small">{settings.notice}</p>}
    {settings?.lastError && !error && <p className="connection-error">上次翻译：{settings.lastError}</p>}
    {error && <p className="connection-error" role="alert">{error}</p>}{message && <p className="connection-message" role="status">{message}</p>}
  </div>;
}
export function ConnectionsPanel({ hub, api, onChanged, onError, includeTranslation = true }) {
  const [draft, setDraft] = useState(() => accountDraft(hub)), [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('');
  const dirty = useRef(false), editRevision = useRef(0);
  useEffect(() => { if (!dirty.current) setDraft(accountDraft(hub)); }, [hub?.settings?.accounts]);
  const request = async (path, body) => {
    if (!api || busy) return;
    const revision = editRevision.current;
    setBusy(true); setError(''); setMessage('');
    try { const result = await api(path, body); onChanged?.(result); if (path === 'hub/configure') { if (editRevision.current === revision) { dirty.current = false; setDraft(accountDraft(result)); } setMessage('账号设置已保存，正在后台读取公开记录。'); } else setMessage(result.sync?.message || '已开始刷新公开记录。'); }
    catch (issue) { setError(issue.message || '未能更新账号，请重试。'); onError?.(issue.message || '未能更新账号'); }
    finally { setBusy(false); }
  };
  return <section className="connection-panel" aria-label="公开账号连接"><div className="progress-section-heading"><h2><UserRound size={17} />平台账号</h2><span>可选</span></div><p className="progress-muted">新增比赛时核对这些账号的原站记录，已通过题自动标记 AC。牛客与洛谷只需用户 ID，不显示账号分数。</p>
    <form onSubmit={event => { event.preventDefault(); request('hub/configure', { accounts: Object.fromEntries(Object.entries(draft).map(([key, value]) => [key, value.trim()])) }); }}>
      <div className="connection-fields">{ACCOUNT_FIELDS.map(([key, name, placeholder]) => <label key={key}><span>{name}</span><input value={draft[key]} onChange={event => { dirty.current = true; editRevision.current += 1; setDraft(value => ({ ...value, [key]: event.target.value })); }} placeholder={placeholder} aria-label={`${name}公开账号`} autoComplete="off" spellCheck={false} /></label>)}</div>
      <div className="progress-actions"><button type="submit" className="progress-button progress-primary" disabled={busy || !api}>{busy ? <LoaderCircle size={14} className="progress-spin" /> : <Check size={14} />}保存账号</button><button type="button" className="progress-button" disabled={busy || hub?.sync?.busy || !api} onClick={() => request('hub/sync', {})}><RefreshCw size={14} />刷新公开记录</button><span className="progress-small">清空后保存，可解除关联。</span></div>
    </form>
    {error && <p className="connection-error" role="alert">{error}</p>}{message && <p className="connection-message" role="status">{message}</p>}
    <div className="connection-account-list">{list(hub?.accounts).filter(account => account.handle && PLATFORMS.some(([key]) => key === account.platform)).map(account => <div className="connection-account" key={account.platform}><div className="connection-account-heading"><strong>{LABELS[account.platform] || account.platform}</strong>{account.url ? <a href={account.url} target="_blank" rel="noreferrer">{account.displayName || account.handle}<ExternalLink size={12} /></a> : <span>{account.displayName || account.handle}</span>}<span className={`connection-status connection-status-${account.status}`}>{({ ready: '已更新', partial: '公开信息有限', error: '暂未读取' })[account.status] || '尚未配置'}</span></div><div className="connection-evidence"><span>评分 <b>{number(account.rating)}</b></span><span>最高 <b>{number(account.maxRating)}</b></span><span>通过 <b>{number(account.solvedCount)}</b></span><span>提交 <b>{number(account.submissionCount)}</b></span><span>{dateLabel(account.updatedAt)}</span></div>{account.error && <p>{account.error}</p>}</div>)}</div>
    {includeTranslation && <TranslationSettings api={api} onError={onError} />}
  </section>;
}

function updateDraft(hub) { return { autoSync: hub?.settings?.autoSync ?? true, intervalHours: hub?.settings?.intervalHours ?? 6, minDifficulty: hub?.settings?.minDifficulty ?? 0, maxDifficulty: hub?.settings?.maxDifficulty ?? 10000 }; }
export function UpdatePanel({ softwareState, hub, api, onChanged, onError, onContent, showNotifications = true, notificationsOnly = false }) {
  const [draft, setDraft] = useState(() => updateDraft(hub)), [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState(''), [unreadOnly, setUnreadOnly] = useState(false);
  const dirty = useRef(false), editRevision = useRef(0);
  useEffect(() => { if (!dirty.current) setDraft(updateDraft(hub)); }, [hub?.settings]);
  const change = (key, value) => { dirty.current = true; editRevision.current += 1; setDraft(previous => ({ ...previous, [key]: value })); };
  const request = async (path, body) => {
    if (!api || busy) return;
    const revision = editRevision.current;
    setBusy(true); setError(''); setMessage('');
    try { const result = await api(path, body); onChanged?.(result); if (path === 'hub/configure') { if (editRevision.current === revision) { dirty.current = false; setDraft(updateDraft(result)); } setMessage('更新偏好已保存。'); } else if (path === 'hub/sync') setMessage(result.sync?.message || '已安排后台检查。'); }
    catch (issue) { setError(issue.message || '未能完成操作，请重试。'); onError?.(issue.message || '未能完成操作'); }
    finally { setBusy(false); }
  };
  const cached = hub?.updates || {}, sync = hub?.sync || {};
  const updates = { ...cached, currentVersion: __TB_VERSION__, latestVersion: softwareState ? softwareState.latestVersion || (softwareState.status === "current" ? `v${softwareState.currentVersion}` : null) : null, url: softwareState?.releaseUrl, notes: softwareState?.notes || "" };
  const notifications = list(hub?.notifications).filter(item => !unreadOnly || !item.read);
  return <section className="update-panel" aria-label="题库与版本更新">{!notificationsOnly&&<><div className="progress-section-heading"><h2><Github size={17} />题库与版本更新</h2><span>当前 {__TB_VERSION__}</span></div>
    <div className="update-project-source"><span>项目公开仓库</span><a href={PROJECT_URL} target="_blank" rel="noreferrer">acm-algo-trainer<ExternalLink size={12} /></a></div>
    {updates.sourceNotice && <p className="progress-small">{updates.sourceNotice}</p>}
    <form onSubmit={event => { event.preventDefault(); request('hub/configure', { ...draft, intervalHours: Number(draft.intervalHours), minDifficulty: Number(draft.minDifficulty), maxDifficulty: Number(draft.maxDifficulty) }); }}>
      <div className="update-options"><label className="progress-check"><input type="checkbox" checked={draft.autoSync} onChange={event => change('autoSync', event.target.checked)} />自动检查已结束的比赛</label><label>检查间隔<BoundedNumber value={draft.intervalHours} min={1} max={24} required unit="h" onChange={event=>change('intervalHours',event.target.value)} aria-label="自动检查间隔"/></label></div>
      <div className="update-difficulty-range"><span>新题难度范围</span><label><span className="update-sr-only">最低难度</span><BoundedNumber type="number" min="0" max="10000" step="1" value={draft.minDifficulty} onChange={event => change('minDifficulty', event.target.value)} aria-label="自动收录最低难度" required /></label><span>至</span><label><span className="update-sr-only">最高难度</span><BoundedNumber type="number" min={Math.max(0, Number(draft.minDifficulty) || 0)} max="10000" step="1" value={draft.maxDifficulty} onChange={event => change('maxDifficulty', event.target.value)} aria-label="自动收录最高难度" required /></label></div>
      <div className="progress-actions"><button type="submit" className="progress-button progress-primary" disabled={busy || !api}><Check size={14} />保存更新偏好</button><button type="button" className="progress-button" disabled={busy || sync.busy || !api} onClick={() => request('hub/sync', {})}>{sync.busy ? <LoaderCircle size={14} className="progress-spin" /> : <RefreshCw size={14} />}现在检查</button></div>
    </form>
    {error && <p className="connection-error" role="alert">{error}</p>}{message && <p className="connection-message" role="status">{message}</p>}
    <div className="update-status"><span>上次检查：{dateLabel(sync.lastCheckedAt || updates.checkedAt)}</span><span>下次检查：{dateLabel(sync.nextCheckAt)}</span>{updates.latestVersion && <span>公开版本：{updates.url ? <a href={updates.url} target="_blank" rel="noreferrer">{updates.latestVersion}<ExternalLink size={12} /></a> : updates.latestVersion}</span>}</div>
    {sync.message && <p className="progress-small">{sync.message}</p>}{updates.error && <p className="connection-error">{updates.error}</p>}
    {list(sync.providers).length > 0 && <div className="update-providers">{list(sync.providers).map(item => <div key={item.platform}><strong>{LABELS[item.platform] || item.platform}</strong><span>{item.message || item.status}</span><small>新增 {number(item.added)} · 待定级 {number(item.pending)}</small></div>)}</div>}
    {updates.notes && <details className="update-release-notes"><summary>版本说明</summary><p>{updates.notes}</p></details>}
</>}
    {showNotifications && <><div className="progress-section-heading update-notification-heading"><h3>更新通知</h3><button type="button" className="progress-text-button" disabled={busy || !api || !list(hub?.notifications).some(item => !item.read)} onClick={() => request('hub/dismiss-all', {})}><CheckCheck size={14} />一键已读</button><label className="progress-check"><input type="checkbox" checked={unreadOnly} onChange={event => setUnreadOnly(event.target.checked)} />只看未读</label></div>
    <div className="update-notifications">{notifications.length ? notifications.map(item => {
      const targets = [...list(item.problemIds), ...list(item.solutionIds), ...list(item.problemUrls)];
      const clickable = targets.length > 0 && Boolean(onContent), Main = clickable ? 'button' : 'div';
      return <div className={`update-notification${item.read ? ' update-read' : ''}`} key={item.id}><span className="update-notification-kind">{({ release: '版本', content: '内容', catalog: '题库' })[item.type] || '更新'}</span><div><Main className="update-notification-main" type={clickable ? 'button' : undefined} onClick={clickable ? () => onContent(item) : undefined}><strong>{item.title}</strong><span className="update-notification-body">{item.body}</span><small>{dateLabel(item.createdAt)}{item.count != null ? ` · ${number(item.count)} 项` : ''}</small></Main><div className="update-notification-actions">{clickable && <button type="button" className="progress-text-button" onClick={() => onContent(item)}>查看新增内容<ArrowRight size={12} /></button>}{item.url && <a href={item.url} target="_blank" rel="noreferrer">{targets.length ? '查看来源' : '在仓库查看'}<ExternalLink size={12} /></a>}{!item.read && <button type="button" className="progress-text-button" disabled={busy || !api} onClick={() => request('hub/dismiss', { id: item.id })}><Check size={12} />标为已读</button>}</div></div></div>;
    }) : <p className="progress-muted">{unreadOnly ? '没有未读通知。' : '新题入库或版本发布后，通知会显示在这里。'}</p>}</div></>}
  </section>;
}
