import {difficultyPresentation} from './difficultyPresentation.js';
// Shared display bands and chronology. Personal submission dates are never
// substituted for the date of the original contest.
export function difficultyBand(value) {
  if (value == null || !Number.isFinite(Number(value))) return "unknown";
  const rating = Number(value);
  return rating < 1200 ? "intro" : rating < 1500 ? "basic" : rating < 1800 ? "intermediate" : rating < 2100 ? "challenge" : "advanced";
}

export function difficultyLabel(row = {},mode='number') {
  if (row.difficultyHidden) return '—';
  return difficultyPresentation(row,mode).label;
}

export function difficultyDescription(row = {}) {
  if (row.difficultyHidden) return row.locked ? '比赛进行中，赛后显示难度' : '完成本场重现赛后显示难度';
  const band = row.difficultyBand;
  return [difficultyPresentation(row).kind==='estimate'?'CF 尺度粗略分档，非官方定级':'', row.difficultySource || '难度待复核',
    Array.isArray(band) ? `参考区间 ${band[0]}–${band[1] ?? '∞'}` : '',
    ...(Array.isArray(row.difficultyEvidence) ? row.difficultyEvidence : [])].filter(Boolean).join(' · ');
}

// Definitions belong to the whole document. Each separately rendered excerpt
// must retain them, even when the definition was below a different heading.
function referenceDefinitions(markdown) {
  const lines = String(markdown).split('\n'), result = [];
  let fence = null;
  for (let i = 0; i < lines.length; i++) {
    const marker = lines[i].match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (marker) {
      if (!fence) fence = marker[1];
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length && !marker[2].trim()) fence = null;
      continue;
    }
    if (fence || !/^ {0,3}\[(?:\\.|[^\\\]])+\]:\s*\S/.test(lines[i])) continue;
    result.push(lines[i]);
    if (/^\s+(?:"[^"\n]*"|'[^'\n]*'|\([^\n]*\))\s*$/.test(lines[i + 1] || '')) result.push(lines[++i]);
  }
  return result.length ? '\n\n' + result.join('\n') : '';
}

export function briefSolution(markdown, difficulty) {
  if (typeof difficulty !== 'number' || difficulty > 1000 || difficulty < 0) return null;
  const lines = String(markdown || '').split('\n'), headings = [];
  let fence = null;
  lines.forEach((line, index) => {
    const code = line.match(/^\s*(`{3,}|~{3,})/);
    if (code) { fence = fence === code[1][0] ? null : fence || code[1][0]; return; }
    const heading = !fence && line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) headings.push({ index, level: heading[1].length, title: heading[2] });
  });
  const section = expression => {
    const heading = headings.find(item => expression.test(item.title));
    if (!heading) return '';
    const end = headings.find(item => item.index > heading.index && item.level <= heading.level)?.index ?? lines.length;
    return lines.slice(heading.index + 1, end).join('\n').trim();
  };
  const paragraph = text => {
    const first = text.split(/\n\s*\n/)[0];
    return (first.match(/(?<!\\)\$/g) || []).length % 2 ? '' : first;
  };
  // Keep complete authored reasoning and diagrams visible in both variants.
  const fullIdea = section(/^(?:思路|做法|算法)/);
  const extraReasoning = headings.some(item => item.level === 3 && !/^(?:题意|思路|做法|算法|从零讲|参考代码|代码实现|代码$|复杂度|易错点)/.test(item.title));
  const intent = paragraph(section(/^题意/)), idea = paragraph(fullIdea);
  if (extraReasoning || fullIdea !== idea || /!\[/.test(fullIdea)) return null;
  const code = section(/(?:参考代码|代码实现|^代码)/).match(/(```(?:cpp|c\+\+|cxx)[^\n]*\n[\s\S]*?\n```)/i)?.[1];
  if (!intent || !idea || !code || intent.length + idea.length > 1200) return null;
  return `### 题意\n\n${intent}\n\n### 思路提要\n\n${idea}\n\n### 参考代码\n\n${code}` + referenceDefinitions(markdown);
}

export function contestTime(row) {
  for (const value of [row?.contestDate, row?.startedAt, row?.endedAt]) {
    if (typeof value !== "string" || !value.trim()) continue;
    const time = Date.parse(value);
    if (Number.isFinite(time)) return time;
  }
  const times = (row?.rows || []).map(contestTime).filter(Number.isFinite);
  return times.length ? Math.max(...times) : null;
}

function roundInfo(row) {
  const name = String(row?.contest || row?.name || "");
  const matches = [...name.matchAll(/\d+/g)];
  const standard = name.match(/(?:Round\s+|ABC\s*|ARC\s*|Div\.\s*[234]\s+|周赛\s*|小白月赛\s*|练习赛\s*|挑战赛\s*|入门赛\s*|基础赛\s*|月赛\s*)(\d+)/i);
  const number = standard ? Number(standard[1]) : matches.length ? Number(matches.at(-1)[0]) : 0;
  const family = String(row?.series || name.replace(/\d+/g, "").replace(/\s+/g, " ").trim());
  return { name, family, number, platform: String(row?.platform || "") };
}

const chronologicalText=new Intl.Collator('zh-CN');
const chronologicalNames=new Intl.Collator('zh-CN',{numeric:true});
function contestOrderKey(row) {
  const time=contestTime(row);
  const eventYear = (row, time) => time != null ? new Date(time).getUTCFullYear() : Number(row.eventYear || row.xcpcYear || row.examYear || row.rows?.find(item => item.eventYear || item.xcpcYear || item.examYear)?.eventYear || row.rows?.[0]?.xcpcYear || row.rows?.[0]?.examYear || 0);
  return {time,year:eventYear(row,time),round:roundInfo(row)};
}
function compareContestKeys(a,b){
  const left=a.time,right=b.time,leftYear=a.year,rightYear=b.year;
  if (leftYear && rightYear && leftYear !== rightYear) return rightYear - leftYear;
  if (left != null && right != null && left !== right) return right - left;
  if (left != null && right == null) return -1;
  if (left == null && right != null) return 1;
  const x = a.round, y = b.round;
  if (x.platform === y.platform && x.family === y.family && x.number !== y.number) return y.number - x.number;
  return chronologicalText.compare(x.platform,y.platform) || chronologicalText.compare(x.family,y.family) || y.number-x.number || chronologicalNames.compare(y.name,x.name);
}
export function compareContestNewest(a,b){return compareContestKeys(contestOrderKey(a),contestOrderKey(b));}
export function createContestComparator(){
 const keys=new WeakMap();
 const key=row=>{if(!keys.has(row))keys.set(row,contestOrderKey(row));return keys.get(row);};
 return (a,b)=>compareContestKeys(key(a),key(b));
}

// Collapse teaching sections in the display layer; the source Markdown stays
// unchanged. Ignore heading-like text inside fenced C++/shell snippets.
export function solutionBlocks(markdown = "", lectures = []) {
  const lines = String(markdown).split("\n"), blocks = [];
  const definitions = referenceDefinitions(markdown);
  let buffered = [], lesson = null, fence = null;
  const flush = () => {
    if (!buffered.length) return;
    blocks.push(lesson ? { type: "lecture", markdown: buffered.join("\n") + definitions, heading: lesson.heading, lecture: lesson.lecture } : { type: "markdown", markdown: buffered.join("\n") + definitions });
    buffered = [];
  };
  for (const line of lines) {
    const code = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (fence) {
      buffered.push(line);
      if (code && code[1][0] === fence[0] && code[1].length >= fence.length && !code[2].trim()) fence = null;
      continue;
    }
    if (code) {
      fence = code[1];
      buffered.push(line);
      continue;
    }
    if (/^\s*<!--\s*reusable-foundations:(?:start|end)\s*-->\s*$/.test(line)) {
      flush();
      lesson = null;
      continue;
    }
    const heading = !fence && line.match(/^(#{1,6})\s+(.+)$/);
    if (heading && lesson && heading[1].length <= lesson.level) { flush(); lesson = null; }
    if (heading && /从零讲\s*[：:]/.test(heading[2])) {
      flush();
      const title = heading[2].replace(/^[\d.、\s]+/, "").replace(/^从零讲\s*[：:]\s*/, "").trim();
      const reference = lectures.find(item => [item.title, item.concept, item.heading].some(name => name && (name === title || name === heading[2] || name.includes(title) || title.includes(name))));
      lesson = { level: heading[1].length, heading: title, lecture: reference };
    }
    buffered.push(line);
  }
  flush();
  return blocks;
}
