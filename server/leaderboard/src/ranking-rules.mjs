export const REWARD_POLICY = Object.freeze({ daily: [100, 60, 30], weekly: [500, 300, 150], timezone: 'Asia/Shanghai', weekStartsOn: 'Sunday' });

export function bounds(period, now) {
  const day = new Date(now + 8 * 3600 * 1000).toISOString().slice(0, 10);
  const startDate = new Date(day + 'T00:00:00Z');
  if (period === 'weekly') startDate.setUTCDate(startDate.getUTCDate() - startDate.getUTCDay());
  const start = startDate.toISOString().slice(0, 10);
  return { day, start, end: addDays(start, period === 'weekly' ? 7 : 1) };
}

export function addDays(day, amount) {
  const date = new Date(day + 'T00:00:00Z');
  date.setUTCDate(date.getUTCDate() + amount);
  return date.toISOString().slice(0, 10);
}

export function rankingQuery(range) {
  const values = range ? [range.start, range.end] : [];
  const sql = `WITH counts AS (
    SELECT e.user_id,COUNT(*) AS count,MAX(e.accepted_at) AS completed_at FROM official_ac_events e
    WHERE NOT EXISTS (SELECT 1 FROM ranking_exclusions x WHERE x.user_id=e.user_id AND x.problem_key=e.problem_key)
    ${range ? 'AND e.accepted_day>=? AND e.accepted_day<?' : ''} GROUP BY e.user_id),
    ranked AS (SELECT users.user_id,users.nickname,counts.count,
      ROW_NUMBER() OVER(ORDER BY counts.count DESC,counts.completed_at,users.user_id) AS position
      FROM counts JOIN users USING(user_id) JOIN accounts USING(user_id))`;
  return { sql, values };
}

export const normalizeRank = row => row && ({ ...row, count: Number(row.count), rank: Number(row.position) });
