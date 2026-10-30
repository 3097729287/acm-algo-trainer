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

export function contestReminderKey(contest) {
  const start = Date.parse(contest?.startAt);
  return contest?.id && Number.isFinite(start) ? `${contest.id}:${start}` : '';
}

function readReminders(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    if (Array.isArray(value)) return new Set(value.filter(item => typeof item === 'string' && item.length < 200).slice(-512));
  } catch { /* Reminders also retain an in-session acknowledgement. */ }
  return new Set();
}

export default function useContestCalendar(api, enabled, open, now, owner = window.__tbAccountUserId || 'local') {
  const [storedSnapshot, setSnapshot] = useState(null), [storedError, setError] = useState(null);
  const [revision, setRevision] = useState(0), forceNext = useRef(false);
  const [clockRevision, tickClock] = useState(0), [reminderRevision, updateReminders] = useState(0);
  const [pendingReminder, setReminder] = useState(null), presented = useRef(new Map());
  const anchor = useRef({ input: now, at: Date.now() });
  if (anchor.current.input !== now) anchor.current = { input: now, at: Date.now() };
  const calendarNow = now + Date.now() - anchor.current.at;
  const key = `tb.contest-calendar.seen.${owner ?? 'anonymous'}`;
  const reminderKey = `tb.contest-calendar.reminders.${owner ?? 'anonymous'}`;
  const currentOwner = useRef(reminderKey); currentOwner.current = reminderKey;
  const snapshot = storedSnapshot?.owner === key ? storedSnapshot.value : null;
  const error = storedError?.owner === key ? storedError.value : '';
  const [seen, setSeen] = useState(() => ({ key, ...readSeen(key) }));
  const today = trainingDay(calendarNow);
  useEffect(() => {
    const update = event => { if (!event || event.key === key) setSeen({ key, ...readSeen(key) }); };
    update();
    window.addEventListener('storage', update);
    return () => window.removeEventListener('storage', update);
  }, [key]);
  useEffect(() => {
    const update = event => { if (event.key === reminderKey) updateReminders(value => value + 1); };
    const wake = () => tickClock(value => value + 1);
    window.addEventListener('storage', update);
    document.addEventListener('visibilitychange', wake);
    window.addEventListener('focus', wake);
    return () => { window.removeEventListener('storage', update); document.removeEventListener('visibilitychange', wake); window.removeEventListener('focus', wake); };
  }, [reminderKey]);
  useEffect(() => {
    if (!enabled) return;
    const moments = (snapshot?.contests || []).flatMap(row => {
      const start = Date.parse(row.startAt);
      return [start - 300000, start, Date.parse(row.endAt)];
    }).filter(moment => Number.isFinite(moment) && moment > calendarNow);
    if (!moments.length) return;
    const timer = setTimeout(() => tickClock(value => value + 1), Math.max(25, Math.min(2147483647, Math.min(...moments) - calendarNow + 25)));
    return () => clearTimeout(timer);
  }, [enabled, snapshot, now, clockRevision]);
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
        setSnapshot({owner:key,value}); setError(null);
        if (value.refreshing || value.importing) delay = 1500;
        const clock = anchor.current.input + Date.now() - anchor.current.at;
        const starts=(value.contests||[]).map(row=>Date.parse(row.startAt)-clock+100).filter(ms=>ms>0);
        delay=Math.max(100,Math.min(delay,...starts));
      } catch (issue) {
        if (!stopped) setError({owner:key,value:issue.message});
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
  }, [api, enabled, open, today, revision, key]);
  const contests = (snapshot?.contests || []).filter(contest => new Date(contest.endAt).getTime() > calendarNow);
  const activeReminder = pendingReminder?.owner === reminderKey && contests.find(contest => contestReminderKey(contest) === pendingReminder.signature);
  const reminder = activeReminder ? { ...activeReminder, signature: pendingReminder.signature, ownerKey: reminderKey } : null;
  useEffect(() => {
    if (!enabled || owner == null || document.hidden) { setReminder(null); return; }
    const saved = readReminders(reminderKey), local = presented.current.get(reminderKey) || new Set();
    if (activeReminder && (!saved.has(pendingReminder.signature) || local.has(pendingReminder.signature))) return;
    const next = contests.filter(contest => Date.parse(contest.startAt) > calendarNow && Date.parse(contest.startAt) - calendarNow <= 300000)
      .sort((a, b) => Date.parse(a.startAt) - Date.parse(b.startAt) || a.id.localeCompare(b.id))
      .find(contest => { const signature = contestReminderKey(contest); return signature && !saved.has(signature) && !local.has(signature); });
    setReminder(next ? { owner: reminderKey, signature: contestReminderKey(next) } : null);
  }, [enabled, owner, reminderKey, snapshot, calendarNow, reminderRevision, clockRevision, pendingReminder]);
  const markReminderShown = useCallback(() => {
    if (!pendingReminder || pendingReminder.owner !== reminderKey || currentOwner.current !== reminderKey) return;
    const local = presented.current.get(reminderKey) || new Set();
    local.add(pendingReminder.signature);
    presented.current.set(reminderKey, new Set([...local].slice(-512)));
    if (presented.current.size > 8) presented.current.delete(presented.current.keys().next().value);
    const saved = readReminders(reminderKey); saved.add(pendingReminder.signature);
    try { localStorage.setItem(reminderKey, JSON.stringify([...saved].slice(-512))); } catch { /* Keep local presentation evidence. */ }
    updateReminders(value => value + 1);
  }, [reminderKey, pendingReminder]);
  const dismissReminder = useCallback(() => {
    markReminderShown();
    setReminder(previous => previous?.owner === reminderKey ? null : previous);
  }, [reminderKey, markReminderShown]);
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
  return { snapshot, contests, error, today, now: calendarNow, hasUnreadToday, markTodaySeen, refresh,
    ownerKey: reminderKey, reminder, markReminderShown, dismissReminder };
}
