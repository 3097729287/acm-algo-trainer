import { AccountError } from './accounts.mjs';

// Deliberately excludes credentials, ranking_profile, pending browser sessions,
// machine settings, API keys, cookies and local filesystem paths.
export const columns = Object.freeze({
  training: 'id active_at solution_pending rewrite_due accepted_at last_local_at last_review_at review_count mock_due solution_seen_at mock_due_at mock_due_context active removed_at',
  practice_sets: 'id name ids created_at',
  contests: 'id name status started_at deadline finished_at duration slots config deleted_at',
  drafts: 'problem_id context code saved_at',
  submissions: 'id problem_id contest_id mode code submitted_at finished_at verdict scope time_ms memory_kb passed total output stderr message custom_input solution_seen sample_run case_results',
  tb_rank_profile: 'id unlocked_at',
  official_first_xp_awards: 'problem_key accepted_at awarded_xp',
  official_xp_state: 'id migrated_at',
  daily_missions: 'day id definition claimed_at awarded_xp evidence',
  goals: 'id created_at config archived',
  goal_daily_assignments: 'goal_id day ids target',
  ranking_receipts: 'endpoint event_id accepted_at',
  ranking_reward_totals: 'endpoint user_id total_xp awards updated_at',
  account_sync_conflicts: 'id data',
  achievement_xp_claims: 'achievement_id unlocked_at awarded_xp claimed_at',
  account_preferences: 'key value updated_at',
  account_problem_facts: 'problem_id value updated_at',
});
export const STATE_LIMIT = 4 * 1024 * 1024;

export function guardStateJson(bytes) {
  // Large messages are shallow gzip envelopes. Count structure before parsing,
  // skipping quoted strings without allocating another buffer. A dense array
  // of millions of tiny objects must never reach JSON.parse in a 64 MiB heap.
  let quoted = false, escaped = false, budget = 0, depth = 0;
  for (const byte of bytes) {
    if (quoted) {
      if (escaped) escaped = false;
      else if (byte === 92) escaped = true;
      else if (byte === 34) quoted = false;
      continue;
    }
    if (byte === 34) { quoted = true; budget++; }
    else if (byte !== 9 && byte !== 10 && byte !== 13 && byte !== 32) {
      budget++;
      if (byte === 91 || byte === 123) depth++;
      else if (byte === 93 || byte === 125) depth--;
    }
    if (budget > 2048 || depth > 8) throw new AccountError(413, '大状态请求只接受浅层压缩信封');
  }
}

export function validateState(value, userId) {
  if (value?.format === 'tb-account-state-gzip-v1') {
    // The server stores compressed account-private state without inflating it
    // in the 64 MiB Node heap. Desktop clients verify its checksum and bounded
    // decoded schema before applying it; no payload executes on the service.
    if (Object.keys(value).some(key => !['format', 'payload', 'sha256', 'uncompressedBytes'].includes(key)) ||
        typeof value.payload !== 'string' || value.payload.length < 1 || value.payload.length > STATE_LIMIT - 2048 ||
        !/^[A-Za-z0-9+/]+={0,2}$/.test(value.payload) || !/^[a-f0-9]{64}$/.test(value.sha256 || '') ||
        !Number.isSafeInteger(value.uncompressedBytes) || value.uncompressedBytes < 1 || value.uncompressedBytes > 64 * 1024 * 1024)
      throw new AccountError(400, '账号压缩同步数据无效');
    return value;
  }
  const raw = JSON.stringify(value);
  if (raw && raw.length > 65536) throw new AccountError(413, '请使用压缩账号同步协议');
  if (!value || value.format !== 'tb-account-state-v1' || !value.tables || typeof value.tables !== 'object' || Array.isArray(value.tables) ||
      Object.keys(value).some(key => !['format', 'tables', 'publicAccounts'].includes(key)) ||
      Object.keys(value.tables).some(key => !Object.hasOwn(columns, key))) throw new AccountError(400, '账号同步数据格式无效');
  for (const [table, rows] of Object.entries(value.tables)) {
    const allowed = columns[table].split(' ');
    if (!Array.isArray(rows) || rows.some(row => !row || typeof row !== 'object' || Array.isArray(row) ||
        Object.keys(row).some(key => !allowed.includes(key)) || Object.values(row).some(item => item !== null && !['number', 'string'].includes(typeof item)) ||
        table === 'ranking_reward_totals' && row.user_id !== userId)) throw new AccountError(400, '账号同步记录字段无效');
  }
  const profiles = value.publicAccounts;
  if (!profiles || typeof profiles !== 'object' || Array.isArray(profiles) || Object.keys(profiles).some(key => !['codeforces', 'atcoder'].includes(key)))
    throw new AccountError(400, '公开账号同步数据无效');
  const allowed = ['platform', 'handle', 'displayName', 'url', 'status', 'rating', 'maxRating', 'rank', 'solvedCount', 'submissionCount', 'updatedAt', 'error', 'history', 'solved', 'activity'];
  for (const [platform, profile] of Object.entries(profiles)) {
    if (!profile || profile.platform !== platform || typeof profile.handle !== 'string' ||
        profile.handle && !/^[A-Za-z0-9_.-]{1,64}$/.test(profile.handle) ||
        Object.keys(profile).some(key => !allowed.includes(key))) throw new AccountError(400, '公开账号同步字段无效');
    for (const key of ['history', 'solved', 'activity']) {
      if (profile[key] != null && (!Array.isArray(profile[key]) || profile[key].length > 100000)) throw new AccountError(400, '公开账号证据过多');
    }
    // Nested evidence only carries the provider's public scalar metadata.
    for (const [key, keys] of [['solved', ['key', 'url', 'title', 'tags', 'difficulty', 'acceptedAt']], ['history', ['date', 'rating', 'contest', 'rank']], ['activity', ['date', 'submissions', 'accepted']]]) {
      if ((profile[key] || []).some(row => !row || typeof row !== 'object' || Array.isArray(row) || Object.keys(row).some(name => !keys.includes(name))))
        throw new AccountError(400, '公开账号证据字段无效');
    }
  }
  return value;
}
