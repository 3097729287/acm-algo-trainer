import Tooltip from './Tooltip.jsx';
export const FLAME_STAGES = [1, 2, 4, 7, 15, 30, 60];
export default function PracticeStreak({ days = 0 }) {
  const count = Math.max(0, Math.floor(Number(days) || 0));
  const stage = Math.max(0, FLAME_STAGES.findLastIndex(value => count >= value));
  return <Tooltip text={`连续练习 ${count} 天 · 每天至少完成一次正式提交，按北京时间计算；今天尚未练习时保留昨天的连续记录。火焰在 1、2、4、7、15、30、60 天成长。`}>
    <span className={`practice-streak flame-stage-${stage}${count ? '' : ' flame-inactive'}`} tabIndex={0} aria-label={`连续练习 ${count} 天`} data-stage={stage + 1}>
      <svg className="streak-flame" viewBox="0 0 48 56" aria-hidden="true"><g className="flame-sparks"><circle cx="9" cy="19" r="1.7"/><circle cx="37" cy="10" r="1.4"/><circle cx="31" cy="3" r="1.2"/></g><path className="flame-outer" d="M25 4c4 13-7 15-3 25 4-1 8-6 8-11 10 9 16 17 12 27-4 12-30 13-36-1C1 32 13 22 15 14c2 5 1 9 3 11C17 17 24 14 25 4Z"/><path className="flame-inner" d="M25 28c1 8 7 8 8 15 1 10-16 12-19 3-3-8 7-12 6-19 3 2 3 6 3 8 2-2 2-4 2-7Z"/></svg><b>{count}</b>
    </span>
  </Tooltip>;
}
