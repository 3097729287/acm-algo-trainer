import {createHash, randomInt, randomUUID} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {AccountError} from './accounts.mjs';

const publicCatalogue = JSON.parse(readFileSync(new URL('./team-contests.json', import.meta.url), 'utf8'));
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const digest = value => createHash('sha256').update(value).digest('hex');
const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
  ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value;
export class TeamError extends AccountError {
  constructor(status, code, message) { super(status, message); this.code = 'TEAM_' + code; }
}
const fail = (status, code, message) => { throw new TeamError(status, code, message); };
const name = value => {
  if (typeof value !== 'string' || !value.isWellFormed() || !value.trim() || [...value.trim()].length > 32 || /[\x00-\x1f\x7f]/u.test(value))
    fail(400, 'NAME_INVALID', '队名须为 1–32 个字');
  return value.trim();
};
const status = (room, now) => room.status === 'finished' || now >= room.deadline ? 'finished'
  : now < room.startedAt ? 'countdown' : 'active';
const iso = value => new Date(value).toISOString();
const leaseValid = (room, owner, token, now) => room.lease?.owner === owner
  && room.lease.token === token && room.lease.until > now;

export class TeamTraining {
  constructor(db, dialect = 'mysql', {catalogue = publicCatalogue, enabled = true} = {}) {
    if (catalogue.schema !== 1 || !Array.isArray(catalogue.contests)) throw Error('Invalid team contest catalogue');
    this.db = db; this.dialect = dialect; this.enabled = enabled; this.catalogue = catalogue;
    this.contests = new Map(catalogue.contests.map(contest => [contest.id, contest]));
    for (const contest of this.contests.values()) {
      if (contest.problems.length < 2 || contest.problems.length > 26 ||
          new Set(contest.problems.map(p => p.id)).size !== contest.problems.length ||
          new Set(contest.problems.map(p => p.problemKey)).size !== contest.problems.length ||
          contest.problems.some(p => !/^[a-f0-9]{64}$/.test(p.problemKey))) throw Error('Invalid team problem identities');
    }
  }
  async available() {
    if (this.schemaReady) return true;
    try {
      for (const table of ['team_lobby', 'teams', 'team_members', 'team_rooms', 'team_room_members', 'team_problems', 'team_drafts', 'team_operations'])
        await this.db.execute(`SELECT 1 FROM ${table} LIMIT 0`);
      this.schemaReady = true;return true;
    } catch (error) {
      if (error.code === 'ER_NO_SUCH_TABLE' || /no such table/i.test(error.message)) return false;
      throw error;
    }
  }
  async transaction(action) {
    return this.db.transaction(async db => {
      await db.execute('SELECT singleton FROM team_lobby WHERE singleton=1' + (this.dialect === 'mysql' ? ' FOR UPDATE' : ''));
      return action(db);
    });
  }
  async session(db, owner, auth, now) {
    await db.execute('SELECT user_id FROM accounts WHERE user_id=?' + (this.dialect === 'mysql' ? ' FOR UPDATE' : ''), [owner]);
    const [rows] = await db.execute('SELECT s.token_hash FROM account_sessions s JOIN accounts a ON a.user_id=s.user_id WHERE s.user_id=? AND s.token_hash=? AND s.expires_at>? AND s.password_version=a.password_version', [owner, auth, Math.floor(now / 1000)]);
    if (!rows.length) fail(401, 'SESSION_EXPIRED', '登录已失效，请重新登录');
  }
  async team(db, owner) {
    const [rows] = await db.execute('SELECT t.payload FROM teams t JOIN team_members m ON m.team_id=t.team_id WHERE m.user_id=? AND t.archived=0', [owner]);
    return rows.length ? JSON.parse(rows[0].payload) : null;
  }
  async room(db, id) {
    if (!id) return null;
    const [rows] = await db.execute('SELECT payload FROM team_rooms WHERE room_id=?', [id]);
    return rows.length ? JSON.parse(rows[0].payload) : null;
  }
  async saveTeam(db, team) {
    await db.execute('UPDATE teams SET archived=?,payload=? WHERE team_id=?', [team.archived ? 1 : 0, JSON.stringify(team), team.id]);
  }
  async saveRoom(db, room, now) {
    await db.execute('UPDATE team_rooms SET status=?,ended_at=?,updated_at=?,payload=? WHERE room_id=?',
      [room.status, iso(room.finishedAt ?? room.deadline), now, JSON.stringify(room), room.id]);
  }
  async scores(db, room, now) {
    const [rows] = await db.execute('SELECT e.user_id,e.problem_key,e.accepted_at FROM official_ac_events e JOIN team_room_members m ON m.user_id=e.user_id JOIN team_problems p ON p.room_id=m.room_id AND p.problem_key=e.problem_key WHERE m.room_id=? AND p.available=1 AND e.accepted_at>=? AND e.accepted_at<=?',
      [room.id, iso(room.startedAt), iso(Math.min(now, room.finishedAt ?? room.deadline))]);
    const first = new Map();
    for (const row of rows) {
      const previous = first.get(row.problem_key);
      if (!previous || row.accepted_at < previous.accepted_at) first.set(row.problem_key, row);
    }
    return {totalScore: first.size, solved: room.problems.filter(p => first.has(p.problemKey)).map(p => ({
      id: p.id, owner: first.get(p.problemKey).user_id, acceptedAt: first.get(p.problemKey).accepted_at}))};
  }
  async viewRoom(db, owner, room, now) {
    if (!room) return null;
    const [members] = await db.execute('SELECT user_id FROM team_room_members WHERE room_id=? AND user_id=?', [room.id, owner]);
    if (!members.length) fail(403, 'ROOM_FORBIDDEN', '你未参加这场团队训练');
    const [drafts] = await db.execute('SELECT language,code,revision,edited_by,updated_at FROM team_drafts WHERE room_id=? AND problem_id=?', [room.id, room.problemId]);
    const document = drafts[0] || {language: 'cpp17', code: '', revision: 0, edited_by: null, updated_at: null};
    const currentStatus = status(room, now);
    return {id: room.id, teamId: room.teamId, teamName: room.teamName, revision: room.revision,
      status: currentStatus, startedAt: room.startedAt, deadline: room.deadline, finishedAt: room.finishedAt ?? (currentStatus === 'finished' ? room.deadline : null),
      contestId: room.contestId, contestTitle: room.contestTitle, problems: room.problems, problemId: room.problemId,
      lease: currentStatus !== 'finished' && room.lease?.until > now ? {
        owner: room.lease.owner, until: room.lease.until, ...(room.lease.owner === owner ? {token: room.lease.token} : {})} : null,
      document: {language: document.language, code: document.code, revision: document.revision,
        editedBy: document.edited_by, savedAt: document.updated_at}, score: await this.scores(db, room, now)};
  }
  async view(db, owner, now) {
    const team = await this.team(db, owner);
    if (!team) return {owner, serverNow: now, enabled: this.enabled, protocol: 1, team: null, room: null};
    const [members] = await db.execute('SELECT m.user_id,m.ready,m.last_seen,m.joined_at,u.nickname,a.hash AS avatar_hash FROM team_members m JOIN users u ON u.user_id=m.user_id LEFT JOIN account_public_avatars a ON a.user_id=m.user_id WHERE m.team_id=? ORDER BY m.joined_at,m.user_id', [team.id]);
    const room = await this.room(db, team.roomId);
    const [participants] = room ? await db.execute('SELECT user_id FROM team_room_members WHERE room_id=? AND user_id=?', [room.id, owner]) : [[]];
    return {owner, serverNow: now, enabled: this.enabled, protocol: 1,
      team: {id: team.id, name: team.name, leader: team.leader, revision: team.revision, inviteCode: team.inviteCode,
        contestId: team.contestId, durationMinutes: team.durationMinutes, catalogueRevision: team.catalogueRevision,
        members: members.map(m => ({owner: m.user_id, nickname: m.nickname, avatarHash: m.avatar_hash,
          ready: Boolean(m.ready), online: now - m.last_seen < 25000}))},
      room: participants.length ? await this.viewRoom(db, owner, room, now) : null};
  }
  async read(owner, now) {
    if (!this.enabled || !await this.available()) return {owner, serverNow: now, enabled: false, protocol: 1, team: null, room: null};
    return this.transaction(db => this.view(db, owner, now));
  }
  async write(owner, auth, action, body, now) {
    if (!this.enabled || !await this.available()) fail(503, 'UNAVAILABLE', '团队训练服务尚未就绪');
    if (!body || typeof body !== 'object' || Array.isArray(body)) fail(400, 'REQUEST_INVALID', '请求内容无效');
    if (action !== 'poll' && !uuid.test(body.requestId || '')) fail(400, 'REQUEST_INVALID', '请求编号无效');
    const requestHash = digest(JSON.stringify(canonical({action, body})));
    return this.transaction(async db => {
      await this.session(db, owner, auth, now);
      if (action !== 'poll') {
        const [previous] = await db.execute('SELECT request_hash,ack FROM team_operations WHERE user_id=? AND request_id=?', [owner, body.requestId]);
        if (previous.length) {
          if (previous[0].request_hash !== requestHash) fail(409, 'REQUEST_CONFLICT', '该请求编号已用于另一项操作');
          return {...await this.view(db, owner, now), ack: JSON.parse(previous[0].ack)};
        }
      }
      let team = await this.team(db, owner);
      let room = await this.room(db, team?.roomId);
      const live = room && status(room, now) !== 'finished';
      const requireTeam = () => { if (!team) fail(409, 'NO_TEAM', '请先加入队伍'); };
      const leader = () => { requireTeam(); if (team.leader !== owner) fail(403, 'LEADER_REQUIRED', '这项操作由队长进行'); };
      const teamRevision = () => { requireTeam(); if (body.teamRevision !== team.revision) fail(409, 'REVISION_CONFLICT', '队伍已更新，请重新读取'); };
      const active = () => {
        requireTeam();
        if (!room || room.id !== body.roomId || status(room, now) !== 'active') fail(409, 'ROOM_LOCKED', '比赛尚未开始或已经结束');
      };
      const editor = () => { active(); if (!leaseValid(room, owner, body.leaseToken, now)) fail(409, 'EDITOR_CHANGED', '编辑控制已变更，代码已保留'); };
      const ack = {requestId: body.requestId ?? null, action};
      if (action === 'create') {
        if (team) fail(409, 'ALREADY_JOINED', '你已加入队伍');
        const alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
        let inviteCode;
        for (let tries = 0; tries < 8; tries++) {
          inviteCode = Array.from({length: 8}, () => alphabet[randomInt(alphabet.length)]).join('');
          const [collision] = await db.execute('SELECT team_id FROM teams WHERE invite_code=?', [inviteCode]);
          if (!collision.length) break;
          inviteCode = null;
        }
        if (!inviteCode) fail(503, 'RETRY', '暂时无法创建队伍，请重试');
        team = {id: randomUUID(), name: name(body.name), leader: owner, inviteCode, revision: 1,
          contestId: null, durationMinutes: 300, catalogueRevision: this.catalogue.revision, roomId: null, archived: false};
        await db.execute('INSERT INTO teams(team_id,invite_code,archived,payload) VALUES(?,?,?,?)', [team.id, inviteCode, 0, JSON.stringify(team)]);
        await db.execute('INSERT INTO team_members(user_id,team_id,ready,last_seen,joined_at) VALUES(?,?,?,?,?)', [owner, team.id, 0, now, now]);
      } else if (action === 'join') {
        if (team) fail(409, 'ALREADY_JOINED', '你已加入队伍');
        const code = typeof body.inviteCode === 'string' ? body.inviteCode.trim().toUpperCase() : '';
        if (!/^[A-Z2-9]{8}$/.test(code)) fail(400, 'INVITE_INVALID', '邀请码无效');
        const [found] = await db.execute('SELECT payload FROM teams WHERE invite_code=? AND archived=0', [code]);
        if (!found.length) fail(404, 'INVITE_INVALID', '未找到这支队伍');
        team = JSON.parse(found[0].payload);room = await this.room(db, team.roomId);
        if (room && status(room, now) !== 'finished') fail(409, 'ROOM_LOCKED', '比赛进行中，交卷后可加入');
        const [members] = await db.execute('SELECT user_id FROM team_members WHERE team_id=?', [team.id]);
        if (members.length >= 3) fail(409, 'TEAM_FULL', '队伍已满三人');
        await db.execute('INSERT INTO team_members(user_id,team_id,ready,last_seen,joined_at) VALUES(?,?,?,?,?)', [owner, team.id, 0, now, now]);
        await db.execute('UPDATE team_members SET ready=0 WHERE team_id=?', [team.id]);
        team.revision++;await this.saveTeam(db, team);
        // A new member cannot receive former participants' private code.
        room = null;
      } else if (action === 'poll') {
        requireTeam();
        await db.execute('UPDATE team_members SET last_seen=? WHERE user_id=? AND team_id=?', [now, owner, team.id]);
        if (body.leaseToken && room && room.id === body.roomId && leaseValid(room, owner, body.leaseToken, now)) {
          room.lease.until = now + 15000;await this.saveRoom(db, room, now);
        }
      } else if (action === 'leave') {
        teamRevision();
        if (live) fail(409, 'ROOM_LOCKED', '比赛进行中，交卷后可离队');
        await db.execute('DELETE FROM team_members WHERE user_id=?', [owner]);
        const [remaining] = await db.execute('SELECT user_id FROM team_members WHERE team_id=? ORDER BY joined_at,user_id', [team.id]);
        if (!remaining.length) team.archived = true;
        else if (team.leader === owner) team.leader = remaining[0].user_id;
        team.revision++;await db.execute('UPDATE team_members SET ready=0 WHERE team_id=?', [team.id]);await this.saveTeam(db, team);
      } else if (action === 'configure') {
        leader();teamRevision();
        if (live) fail(409, 'ROOM_LOCKED', '比赛进行中，交卷后可更换');
        if (!this.contests.has(body.contestId) || !Number.isInteger(body.durationMinutes) || body.durationMinutes < 5 || body.durationMinutes > 300)
          fail(400, 'CONTEST_INVALID', '请选择现有比赛及 5–300 分钟时长');
        team.contestId = body.contestId;team.durationMinutes = body.durationMinutes;team.catalogueRevision = this.catalogue.revision;
        team.revision++;await db.execute('UPDATE team_members SET ready=0 WHERE team_id=?', [team.id]);await this.saveTeam(db, team);
      } else if (action === 'ready') {
        teamRevision();
        if (live || !team.contestId || typeof body.ready !== 'boolean') fail(409, 'ROOM_LOCKED', '请先选择比赛');
        await db.execute('UPDATE team_members SET ready=?,last_seen=? WHERE user_id=?', [body.ready ? 1 : 0, now, owner]);
        team.revision++;await this.saveTeam(db, team);
      } else if (action === 'start') {
        leader();teamRevision();
        if (live) fail(409, 'ROOM_LOCKED', '已有进行中的团队训练');
        const contest = this.contests.get(team.contestId);
        if (!contest || team.catalogueRevision !== this.catalogue.revision) fail(409, 'CATALOGUE_CHANGED', '比赛目录已更新，请重新选择');
        const [members] = await db.execute('SELECT user_id,ready,last_seen FROM team_members WHERE team_id=?', [team.id]);
        if (members.length !== 3 || members.some(m => !m.ready || now - m.last_seen >= 25000)) fail(409, 'NOT_READY', '需要三名队员在线并准备');
        room = {id: randomUUID(), teamId: team.id, teamName: team.name, revision: 1, status: 'active', startedAt: now + 3000,
          deadline: now + 3000 + team.durationMinutes * 60000, finishedAt: null, contestId: contest.id, contestTitle: contest.title,
          problems: structuredClone(contest.problems), problemId: contest.problems.find(p => p.available)?.id, lease: null};
        if (!room.problemId) fail(409, 'NO_PROBLEMS', '这场比赛的题面暂不可用');
        await db.execute('INSERT INTO team_rooms(room_id,team_id,status,started_at,deadline,ended_at,updated_at,payload) VALUES(?,?,?,?,?,?,?,?)',
          [room.id, team.id, room.status, iso(room.startedAt), room.deadline, iso(room.deadline), now, JSON.stringify(room)]);
        for (const member of members) await db.execute('INSERT INTO team_room_members(room_id,user_id) VALUES(?,?)', [room.id, member.user_id]);
        for (const p of room.problems) await db.execute('INSERT INTO team_problems(room_id,problem_id,problem_key,available) VALUES(?,?,?,?)', [room.id, p.id, p.problemKey, p.available ? 1 : 0]);
        team.roomId = room.id;team.revision++;await this.saveTeam(db, team);
        await db.execute('UPDATE team_members SET ready=0 WHERE team_id=?', [team.id]);
      } else if (action === 'claim') {
        active();
        if (room.lease?.until > now && room.lease.owner !== owner) fail(409, 'EDITOR_BUSY', '队友正在编辑');
        if (room.lease?.owner !== owner || room.lease.until <= now) {
          room.lease = {owner, token: randomUUID(), until: now + 15000};room.revision++;await this.saveRoom(db, room, now);
        }
      } else if (action === 'release') {
        editor();room.lease = null;room.revision++;await this.saveRoom(db, room, now);
      } else if (action === 'select') {
        editor();
        if (!room.problems.some(p => p.id === body.problemId && p.available)) fail(422, 'PROBLEM_UNAVAILABLE', '该题题面暂不可用');
        room.problemId = body.problemId;room.revision++;await this.saveRoom(db, room, now);
      } else if (action === 'draft') {
        editor();
        if (!room.problems.some(p => p.id === body.problemId && p.available)) fail(422, 'PROBLEM_UNAVAILABLE', '该题题面暂不可用');
        if (!['cpp17', 'python3'].includes(body.language) || typeof body.code !== 'string' || !body.code.isWellFormed()
            || Buffer.byteLength(body.code) > 65536 || body.code.includes('\0') || !Number.isInteger(body.revision)) fail(400, 'CODE_INVALID', '代码或语言无效');
        const [drafts] = await db.execute('SELECT revision FROM team_drafts WHERE room_id=? AND problem_id=?', [room.id, body.problemId]);
        const revision = drafts[0]?.revision ?? 0;
        if (body.revision !== revision) fail(409, 'REVISION_CONFLICT', '共享代码已更新，请先查看当前版本');
        if (drafts.length) await db.execute('UPDATE team_drafts SET language=?,code=?,revision=?,edited_by=?,updated_at=? WHERE room_id=? AND problem_id=?', [body.language, body.code, revision + 1, owner, now, room.id, body.problemId]);
        else await db.execute('INSERT INTO team_drafts(room_id,problem_id,language,code,revision,edited_by,updated_at) VALUES(?,?,?,?,?,?,?)', [room.id, body.problemId, body.language, body.code, 1, owner, now]);
        ack.documentRevision = revision + 1;ack.inputSha256 = digest(body.code);
      } else if (action === 'finish') {
        leader();
        if (!room || room.id !== body.roomId) fail(409, 'ROOM_LOCKED', '没有这场团队训练');
        if (now < room.startedAt) fail(409, 'ROOM_LOCKED', '比赛尚未开始');
        if (status(room, now) !== 'finished') {
          room.status = 'finished';room.finishedAt = Math.max(room.startedAt, Math.min(now, room.deadline));room.lease = null;room.revision++;
          await this.saveRoom(db, room, now);team.revision++;await this.saveTeam(db, team);
        }
      } else fail(404, 'ROUTE_NOT_FOUND', '没有找到这项团队操作');
      if (action !== 'poll') await db.execute('INSERT INTO team_operations(user_id,request_id,request_hash,ack,created_at) VALUES(?,?,?,?,?)', [owner, body.requestId, requestHash, JSON.stringify(ack), now]);
      return {...await this.view(db, owner, now), ack};
    });
  }
  async history(owner, now, roomId = null) {
    if (roomId) {
      const room = await this.room(this.db, roomId);
      if (!room) fail(404, 'ROOM_NOT_FOUND', '没有找到这场团队训练');
      return {owner, serverNow: now, room: await this.viewRoom(this.db, owner, room, now)};
    }
    const [rows] = await this.db.execute('SELECT r.payload FROM team_rooms r JOIN team_room_members m ON m.room_id=r.room_id WHERE m.user_id=? ORDER BY r.updated_at DESC,r.room_id DESC LIMIT 20', [owner]);
    return {owner, serverNow: now, rooms: await Promise.all(rows.map(async row => {
      const room = JSON.parse(row.payload), currentStatus = status(room, now);
      return {id: room.id, teamId: room.teamId, teamName: room.teamName, contestTitle: room.contestTitle,
        status: currentStatus, startedAt: room.startedAt, deadline: room.deadline,
        finishedAt: room.finishedAt ?? (currentStatus === 'finished' ? room.deadline : null),
        score: await this.scores(this.db, room, now)};
    }))};
  }
  async standings(now) {
    if (!this.enabled || !await this.available()) fail(503, 'UNAVAILABLE', '团队训练服务尚未就绪');
    const identity = this.dialect === 'mysql' ? "CONCAT(r.room_id,':',p.problem_id)" : "r.room_id||':'||p.problem_id";
    const [rows] = await this.db.execute(`SELECT t.team_id,t.payload,COUNT(DISTINCT CASE WHEN e.event_id IS NOT NULL THEN ${identity} ELSE NULL END) AS total_score FROM teams t LEFT JOIN team_rooms r ON r.team_id=t.team_id LEFT JOIN team_room_members m ON m.room_id=r.room_id LEFT JOIN team_problems p ON p.room_id=r.room_id AND p.available=1 LEFT JOIN official_ac_events e ON e.user_id=m.user_id AND e.problem_key=p.problem_key AND e.accepted_at>=r.started_at AND e.accepted_at<=r.ended_at AND e.accepted_at<=? WHERE t.archived=0 GROUP BY t.team_id,t.payload ORDER BY total_score DESC,t.team_id LIMIT 100`, [iso(now)]);
    return {serverNow: now, source: 'stored-official-first-ac', entries: rows.map(row => ({
      teamId: row.team_id, name: JSON.parse(row.payload).name, totalScore: Number(row.total_score)}))};
  }
}
