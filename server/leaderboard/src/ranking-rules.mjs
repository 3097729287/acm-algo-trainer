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

export function rankingQuery(range, loginDay = null) {
  const values = range ? [range.start, range.end] : [];
  if (loginDay) values.push(loginDay);
  const sql = `WITH counts AS (
    SELECT e.user_id,COUNT(*) AS count,MAX(e.accepted_at) AS completed_at FROM official_ac_events e
    WHERE NOT EXISTS (SELECT 1 FROM ranking_exclusions x WHERE x.user_id=e.user_id AND x.problem_key=e.problem_key)
    ${range ? 'AND e.accepted_day>=? AND e.accepted_day<?' : ''} GROUP BY e.user_id),
    participants AS (SELECT users.user_id,users.nickname,COALESCE(counts.count,0) AS count,
      COALESCE(counts.completed_at,users.created_at) AS completed_at
      FROM users JOIN accounts USING(user_id) LEFT JOIN counts USING(user_id)
      WHERE counts.user_id IS NOT NULL ${loginDay ? 'OR EXISTS(SELECT 1 FROM account_login_days l WHERE l.user_id=users.user_id AND l.day=?)' : ''}),
    ranked AS (SELECT participants.*,
      ROW_NUMBER() OVER(ORDER BY count DESC,completed_at,user_id) AS position FROM participants)`;
  return { sql, values };
}

export const normalizeRank = row => row && ({ ...row, count: Number(row.count), rank: Number(row.position) });
