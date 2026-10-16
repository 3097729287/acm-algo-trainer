import { matches } from "./model.js";
import { compareContestNewest } from "@/lib/practiceMetadata.js";
import { trainingDay } from "@/lib/trainingDate.js";
import { matchesShelf } from "@/lib/contestShelves.js";

export const QUEUES = [
  {
    id: "fill",
    name: "待攻克",
    description: "从上次未通过的地方继续",
    color: "orange",
  },
  {
    id: "verify",
    name: "待验证",
    description: "样例已通过，继续验证完整约束",
    color: "blue",
  },
  {
    id: "review",
    name: "间隔复习",
    description: "首次通过 7 天后，再独立写一次",
    color: "blue",
  },
  {
    id: "check",
    name: "巩固抽检",
    description: "复习通过 30 天后，检查掌握",
    color: "green",
  },
];
export const VERDICTS = {
  AC: "AC",
  SAMPLE_PASS: "样例通过",
  RUN_OK: "运行完成（未校验）",
  WA: "WA",
  TLE: "TLE",
  MLE: "MLE",
  RE: "RE",
  CE: "CE",
  OLE: "OLE",
  ERROR: "SE",
  RUNNING: "评测中",
  QUEUED: "排队中",
};
export function verdictLabel(value) {
  return VERDICTS[value] || value || "未提交";
}
export function verdictTone(value) {
  if (value === "AC") return "success";
  if (value === "SAMPLE_PASS" || ["运行完成", "RUN_OK"].includes(value)) return "sample";
  if (["QUEUED", "RUNNING"].includes(value)) return "pending";
  if (value === "WA") return "wrong";
  if (value === "RE") return "runtime";
  if (["TLE", "MLE", "OLE"].includes(value)) return "limit";
  if (value === "CE") return "compile";
  return value ? "failed" : "neutral";
}
export function isTodayTraining(row, now) {
  if (typeof row.today === "boolean") return row.today;
  const day = trainingDay(now);
  return !!row.queue || [row.lastActivityAt, row.lastSubmittedAt, row.activeAt]
    .some(value => value && trainingDay(value) === day);
}

export function trainingPriority(row) {
  const rank = QUEUES.findIndex(queue => queue.id === row.queue);
  return rank >= 0 ? rank : QUEUES.length + Number(!!row.accepted);
}

export function groupSubmissionsByDay(submissions) {
  const groups = new Map();
  for (const submission of [...submissions].sort((a, b) => (Date.parse(b.submittedAt) || 0) - (Date.parse(a.submittedAt) || 0))) {
    const day = trainingDay(submission.submittedAt);
    if (!groups.has(day)) groups.set(day, { day, submissions: [], problems: new Set(), accepted: new Set() });
    const group = groups.get(day);
    group.submissions.push(submission);
    group.problems.add(submission.problemId);
    if (submission.verdict === "AC" && submission.scope === "official") group.accepted.add(submission.problemId);
  }
  return [...groups.values()];
}
export function progressMap(workspace) {
  return new Map((workspace?.training || []).map((row) => [row.id, row]));
}
// Polling updates the server clock, but usually leaves training unchanged.
// Preserve equal subtrees so a clock tick does not rebuild the whole catalog.
export function shareWorkspace(previous, next) {
  if (previous === next) return previous;
  if (previous == null || next == null || typeof previous !== 'object' || typeof next !== 'object') return next;
  if (Array.isArray(previous) !== Array.isArray(next)) return next;
  const keys = Object.keys(next);
  let equal = keys.length === Object.keys(previous).length;
  const result = Array.isArray(next) ? [] : {};
  for (const key of keys) {
    result[key] = shareWorkspace(previous[key], next[key]);
    if (!Object.hasOwn(previous, key) || result[key] !== previous[key]) equal = false;
  }
  return equal ? previous : result;
}
export function progressRows(library, workspace) {
  const states = progressMap(workspace);
  const locked = new Set((workspace?.activeContest?.slots || []).map(s=>s.id));
  const known = new Set(library.map(row => row.id));
  const rows = library.concat([...states.values()].filter(row => !known.has(row.id)));
  return rows.map((row) => ({
    ...row,
    ...states.get(row.id),
    active: states.has(row.id),
    verdict: states.get(row.id)?.verdict || null,
    accepted: !!states.get(row.id)?.accepted,
    ...(locked.has(row.id) ? {difficulty:null,tags:[],knowledge:"",locked:true} : {}),
  }));
}
export function filterRows(rows, filters = {}) {
  const {
    query = "",
    platform = "",
    shelf = 'all',
    category = null,
    min = "",
    max = "",
    result = "",
    favoritesOnly = false,
    favorites = [],
    contest = "",
    sort = "contestDate",
    ids = null,
    desc = false,
  } = filters;
  return rows
    .filter(
      (row) =>
        (!ids || ids.includes(row.id)) &&
        matches({ ...row, status: verdictLabel(row.verdict) }, query) &&
        (!platform || row.platform === platform) &&
        matchesShelf(row, shelf) &&
        (!category || row.tags.some((tag) => category.tags.includes(tag))) &&
        (min === "" ||
          (row.difficulty != null && row.difficulty >= Number(min))) &&
        (max === "" ||
          (row.difficulty != null && row.difficulty <= Number(max))) &&
        (!contest || row.contest === contest) &&
        (!favoritesOnly || favorites.includes(row.id)) &&
        (!result ||
          (result === "accepted"
            ? row.accepted
            : result === "pending"
              ? !row.accepted
              : result === "sample"
                ? row.verdict === "SAMPLE_PASS"
                : row.verdict === result)),
    )
    .sort((a, b) => {
      let order = 0;
      if (sort === "contestDate")
        order = compareContestNewest(a, b) || String(a.problem).localeCompare(String(b.problem), "en", { numeric: true });
      else if (sort === "difficulty")
        order = (a.difficulty ?? 9999) - (b.difficulty ?? 9999);
      else if (sort === "date")
        order = (a.lastSubmittedAt || a.activeAt || "").localeCompare(
          b.lastSubmittedAt || b.activeAt || "",
        );
      else if (sort === "title")
        order = a.title.localeCompare(b.title, "zh-CN");
      else
        order =
          a.contest.localeCompare(b.contest, "zh-CN", { numeric: true }) ||
          a.problem.localeCompare(b.problem, "en", { numeric: true });
      return desc ? -order : order;
    });
}
export function groupContests(rows) {
  const groups = new Map();
  for (const row of rows) {
    if (!groups.has(row.contest))
      groups.set(row.contest, {
        name: row.contest,
        platform: row.platform,
        rows: [],
      });
    groups.get(row.contest).rows.push(row);
  }
  return [...groups.values()].map((group) => ({
    ...group,
    total: group.rows.length,
    accepted: group.rows.filter((r) => r.accepted).length,
    active: group.rows.filter((r) => r.active).length,
    min: Math.min(...group.rows.map((r) => r.difficulty ?? Infinity)),
    max: Math.max(...group.rows.map((r) => r.difficulty ?? 0)),
    tags: [...new Set(group.rows.flatMap((r) => r.tags))],
  }));
}
export function categoryCounts(node, rows, training) {
  const has = (row) => row.tags.some((tag) => node.tags.includes(tag));
  const active = training.filter(has);
  return {
    available: rows.filter(row => !row.catalogHidden && has(row)).length,
    active: active.length,
    accepted: active.filter((r) => r.accepted).length,
    due: active.filter((r) => r.queue).length,
  };
}
export function remainingSeconds(contest, now = Date.now()) {
  if (!contest || contest.status !== "running") return 0;
  return Math.max(0, Math.ceil((Date.parse(contest.deadline) - now) / 1000));
}
export function timerText(seconds) {
  const value = Math.max(0, Math.floor(seconds));
  return [Math.floor(value / 3600), Math.floor((value % 3600) / 60), value % 60]
    .map((v) => String(v).padStart(2, "0"))
    .join(":");
}
export function nextSurviving(ids, currentId, remaining) {
  const position = ids.indexOf(currentId),
    valid = new Set(remaining);
  return (
    ids.slice(position + 1).find((id) => valid.has(id)) ||
    ids
      .slice(0, position)
      .reverse()
      .find((id) => valid.has(id)) ||
    remaining[0] ||
    null
  );
}
export const emptyWorkspace = {
  training: [],
  sets: [],
  contests: [],
  activeContest: null,
  summary: {
    total: 0,
    accepted: 0,
    samplePassed: 0,
    attempts: 0,
    due: 0,
    streak: 0,
  },
};
