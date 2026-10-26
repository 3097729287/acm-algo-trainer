import { useCallback, useEffect, useRef, useState } from 'react';
import { trainingDay } from './trainingDate.js';

export function relativeContestDay(day, today) {
  const days = Math.round((new Date(`${day}T00:00:00+08:00`) - new Date(`${today}T00:00:00+08:00`)) / 86400000);
  return days <= 0 ? '今天' : ['今天', '明天', '后天'][days] || `${days}天后`;
}

function readSeen(key) {
  try {
    const saved = JSON.parse(localStorage.getItem(key));
    if (saved && typeof saved.day === 'string' && Array.isArray(saved.ids))
      return { day: saved.day, ids: saved.ids.filter(id => typeof id === 'string').slice(-256) };
  } catch { /* A blocked browser store must not prevent opening the calendar. */ }
  return { day: '', ids: [] };
}

export default function useContestCalendar(api, enabled, open, now) {
  const [snapshot, setSnapshot] = useState(null), [error, setError] = useState('');
  const [revision, setRevision] = useState(0), forceNext = useRef(false);
  const key = `tb.contest-calendar.seen.${window.__tbAccountUserId || 'local'}`;
  const [seen, setSeen] = useState(() => ({ key, ...readSeen(key) }));
  const today = trainingDay(now);
  useEffect(() => {
    const update = event => { if (!event || event.key === key) setSeen({ key, ...readSeen(key) }); };
    update();
    window.addEventListener('storage', update);
    return () => window.removeEventListener('storage', update);
  }, [key]);
  useEffect(() => {
    if (!enabled) return;
    let stopped = false, pending = false, timer;
    async function load() {
      if (stopped || pending) return;
      clearTimeout(timer);
      if (document.hidden) return;
      pending = true;
      let delay = open ? 30000 : 60000;
      const force = forceNext.current;
      forceNext.current = false;
      try {
        const value = await api('contest-calendar' + (force ? '?refresh=1' : ''));
        if (stopped) return;
        setSnapshot(value); setError('');
        if (value.refreshing || open && value.importing) delay = 1500;
      } catch (issue) {
        if (!stopped) setError(issue.message);
      } finally {
        pending = false;
        if (!stopped) timer = setTimeout(load, delay);
      }
    }
    const wake = () => { if (!document.hidden) load(); };
    load();
    document.addEventListener('visibilitychange', wake);
    window.addEventListener('focus', wake);
    return () => { stopped = true; clearTimeout(timer); document.removeEventListener('visibilitychange', wake); window.removeEventListener('focus', wake); };
  }, [api, enabled, open, today, revision]);
  const contests = (snapshot?.contests || []).filter(contest => new Date(contest.endAt).getTime() > now);
  const todayIds = contests.filter(contest => trainingDay(contest.startAt) <= today).map(contest => contest.id);
  const hasUnreadToday = todayIds.some(id => seen.key !== key || seen.day !== today || !seen.ids.includes(id));
  const markTodaySeen = () => {
    if (!hasUnreadToday) return;
    const saved = readSeen(key);
    const value = { day: today, ids: [...new Set([...(saved.day === today ? saved.ids : []), ...todayIds])].slice(-256) };
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Retain the in-session acknowledgement. */ }
    setSeen({ key, ...value });
  };
  const refresh = useCallback(() => { forceNext.current = true; setRevision(value => value + 1); }, []);
  return { snapshot, contests, error, today, now, hasUnreadToday, markTodaySeen, refresh };
}
