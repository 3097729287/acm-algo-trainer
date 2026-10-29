import {catalogSegments} from './contestCatalog.js';

export function completedReplayContests(workspace = {}) {
  // The server includes finished replays whose history entry was later hidden.
  // Visible records also support older workspace responses and local fixtures.
  return new Set([
    ...(workspace.completedReplayContests || []),
    ...(workspace.contests || []).filter(contest => contest.status === 'finished'
      && contest.strategy === 'replay').map(contest => contest.constraints?.contest),
  ].filter(name => typeof name === 'string' && name.length));
}

export function hidesContestDifficulty(row, completed) {
  return catalogSegments(row)[0] === 'XCPC' && !completed.has(row.contest);
}
