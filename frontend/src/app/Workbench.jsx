import {matchesShortcut} from '@/lib/shortcuts.js';
import ThemedSelect from '@/components/ThemedSelect.jsx';
import BoundedNumber from '@/components/BoundedNumber.jsx';
import { memo, useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {
  ArrowLeft, ArrowRight, BookOpen, Check, ChevronDown, ChevronUp,
  Code2, Copy, ExternalLink, History, LoaderCircle,
  PanelLeft, PanelsTopLeft, Play, RotateCcw, Send, Terminal,
} from 'lucide-react';
import { normalizeMarkdown } from '@/lib/normalizeMarkdown.js';
import { normalizeStatement } from '@/lib/normalizeStatement.js';
import { primeAcceptedSound, playAcceptedSound } from '@/lib/acceptedSound.js';
import { verdictLabel } from '@/models/workspaceModel.js';
import CodeEditor from '@/components/CodeEditor.jsx';
import InlineTitle from '@/components/InlineTitle.jsx';
import ReadingImage, {readingUrlTransform} from '@/components/ReadingImage.jsx';
import './Workbench.css';

const TEMPLATE = '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    \n    return 0;\n}\n';
const PYTHON_TEMPLATE = 'import sys\n\ndef solve():\n    pass\n\nif __name__ == "__main__":\n    solve()\n';
const MAX_BYTES = 64 * 1024;
const byteLength = value => new TextEncoder().encode(value).byteLength;
const STATEMENT_FONT_KEY = 'tb.statement-font-size';
const STATEMENT_FONT_SIZES = [14, 16, 18, 20, 22, 24, 26, 28, 30, 32];
function readStatementFontSize() {
  try {
    const saved = Number(localStorage.getItem(STATEMENT_FONT_KEY));
    if (Number.isInteger(saved) && saved >= 14 && saved <= 32) return saved;
  } catch { /* Reading remains available when browser storage is disabled. */ }
  const uiSize = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui-font-size')) || 16;
  return Math.min(32, Math.max(16, Math.round(uiSize / 2) * 2));
}
const OFFICIAL_STATES = { awaiting_submit: '请在官网提交', loading: '打开浏览器原站', needs_browser: '需要连接浏览器', needs_login: '请在浏览器登录', needs_verification: '请在浏览器验证', ready: '已连接，可提交', submitted: '等待原站受理', judging: '评测中', finished: '评测完成', unconfirmed: '正在核对提交', error: '提交异常', closed: '会话已结束' };
const OFFICIAL_TERMINAL = new Set(['finished', 'error', 'closed']);

// Serialize saves across mounts as well as edits. An older request must never
// finish after a newer draft for the same problem and overwrite it on disk.
const draftQueues = new Map();
const latestDraftRevision = new Map();
let draftRevision = 0;
function touchDraft(record) {
  record.revision = ++draftRevision;
  latestDraftRevision.set(record.key, record.revision);
}
function queuedSave(key, body, api, revision) {
  const previous = draftQueues.get(key) || Promise.resolve();
  const request = previous.catch(() => undefined).then(() => {
    // A retired editor may still be draining its save loop after this problem
    // has been reopened. Its queued snapshot must not overwrite newer edits.
    if ((latestDraftRevision.get(key) || 0) > revision) return { skipped: true };
    return api('draft', body);
  });
  draftQueues.set(key, request);
  const clear = () => { if (draftQueues.get(key) === request) draftQueues.delete(key); };
  request.then(clear, clear);
  return request;
}
function draftKey(id, contestId) {
  const legacy = `tb.draft.v2.${encodeURIComponent(contestId || 'solo')}.${encodeURIComponent(id)}`;
  const account = window.__tbAccountUserId;
  if (!account) return legacy;
  const key = `tb.draft.v3.${account}.${encodeURIComponent(contestId || 'solo')}.${encodeURIComponent(id)}`;
  try {
    // Only the account owning the old personal database may recover its browser
    // drafts. Copy first; keep the pre-upgrade backup intact.
    if (window.__tbOriginalWorkspace && !localStorage.getItem(key) && localStorage.getItem(legacy))
      localStorage.setItem(key, localStorage.getItem(legacy));
  } catch { /* The SQLite draft remains available. */ }
  return key;
}

export async function saveBeforeUpdate(message = '草稿尚未保存，保存成功后会自动继续更新。') {
  const pending = [];
  window.dispatchEvent(new CustomEvent('tb-before-update', { detail: { waitUntil: promise => pending.push(promise) } }));
  const result = await Promise.all([...pending, ...draftQueues.values()]);
  if (result.some(value => value === false)) throw new Error(message);
}
export async function saveBeforeLogout() {
  await saveBeforeUpdate('草稿尚未保存，请保存成功后再退出账号。');
}
function readDraft(key) {
  try {
    const value = JSON.parse(localStorage.getItem(key));
    return value && typeof value.code === 'string' ? value : null;
  } catch { return null; }
}
function retainDraft(record, dirty = true) {
  try {
    localStorage.setItem(record.key, JSON.stringify({
      code: record.code, language:record.language || "cpp17", dirty, owner: record.owner, version: record.version,
      modifiedAt: Date.now(),
    }));
    record.retained = true;
    return true;
  } catch {
    record.retained = false;
    return false;
  }
}
function markDraftSaved(record, version) {
  const value = readDraft(record.key);
  if (value?.owner === record.owner && value.version === version) retainDraft(record, false);
}
function submissionPending(submission) {
  return !submission.finishedAt && ['QUEUED', 'RUNNING'].includes(submission.verdict);
}
function mergeSubmission(rows, submission) {
  const previous = rows.find(row => row.id === submission.id);
  if (previous && (previous.finishedAt && !submission.finishedAt || previous.verdict === 'RUNNING' && submission.verdict === 'QUEUED')) return rows;
  return [submission, ...rows.filter(row => row.id !== submission.id)]
    .sort((a, b) => String(b.submittedAt || '').localeCompare(String(a.submittedAt || '')));
}
function verdictText(submission) {
  if (!submission) return '尚未运行';
  // 旧记录里的本地 AC（scope=local + verdict=AC）现在只算样例通过，不叫 AC。
  if (submission.verdict === 'AC' && submission.scope && submission.scope !== 'official') return '样例通过（旧本地记录）';
  return verdictLabel(submission.verdict);
}
function dateText(value) {
  if (!value) return '';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}
function elapsedText(timeMs) {
  if (timeMs == null) return null;
  return timeMs < 1000 ? `${Math.round(timeMs)} ms` : `${(timeMs / 1000).toFixed(2)} s`;
}
function queryPath(path, id, contestId, reviewId) {
  return `${path}?id=${encodeURIComponent(id)}${contestId ? `&contestId=${encodeURIComponent(contestId)}` : ''}${reviewId ? `&reviewId=${encodeURIComponent(reviewId)}` : ''}`;
}
function requestBody(record, extra = {}) {
  return { id: record.id, language:record.language || "cpp17", ...(record.contestId ? { contestId: record.contestId } : {}), ...(record.reviewId ? {reviewId:record.reviewId} : {}), ...extra };
}

function Verdict({ submission }) {
  const pending = submission && submissionPending(submission);
  const accepted = submission?.verdict === 'AC' && submission.scope === 'official';
  return <span className={`wb-verdict wb-verdict-${String(submission?.verdict || 'none').toLowerCase()}${accepted ? ' wb-verdict-confirmed' : ''}`}>
    {pending && <LoaderCircle size={13} className="wb-spinner" aria-hidden="true" />}
    {submission?.verdict === 'AC' && (!submission.scope || submission.scope === 'official') && <Check size={13} aria-hidden="true" />}
    {verdictText(submission)}
  </span>;
}

// The statement can contain substantial math. Editing code or moving the
// caret must not parse and typeset the same document again.
function StatementPre({ children }) {
  const [copied, setCopied] = useState(false);
  const value = String(children?.props?.children ?? '');
  return <div className="wb-statement-code"><button className="wb-statement-copy" aria-label={copied ? '已复制' : '复制样例或代码'} onClick={async () => { try { await navigator.clipboard.writeText(value); setCopied(true); } catch { setCopied(false); } }}>{copied ? <Check size={14}/> : <Copy size={14}/>}</button><pre tabIndex={0}>{children}</pre></div>;
}
const StatementMarkdown = memo(function StatementMarkdown({ markdown, samples, title, images }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[[rehypeKatex, { throwOnError: false, strict: false, trust: false }]]}
    urlTransform={readingUrlTransform} components={{ pre: StatementPre, img: ({node,...props})=><ReadingImage {...props} images={images}/>, a: ({ node, ...props }) => <a {...props} target="_blank" rel="noreferrer" /> }}>{normalizeMarkdown(normalizeStatement(markdown, samples, title))}</ReactMarkdown>;
});

function CaseResults({ cases }) {
  const lines = value => String(value ?? '').replace(/\r\n?/g, '\n').replace(/\n$/, '').split('\n');
  return <div className="wb-case-results" aria-label="逐例运行结果">{cases.map((item, index) => {
    const known = item.expected != null, expected = lines(item.expected), actual = lines(item.actual);
    const mismatch = known && item.verdict === 'WA';
    const failed = !['AC', 'SAMPLE_PASS', 'RUN_OK'].includes(item.verdict);
    const name = item.name || (known ? `样例 ${index + 1}` : '自定义输入');
    const renderOutput = (values, other, label) => <pre tabIndex={0} aria-label={`${name} ${label}`}>{Array.from({ length: mismatch ? Math.max(values.length, other.length) : values.length }, (_, line) => {
      const differs = mismatch && values[line] !== other[line];
      return <span className={`wb-case-line${differs ? ' wb-case-mismatch' : ''}`} key={line}><i aria-hidden="true">{line + 1}</i><span>{values[line] ?? '（无此行）'}{values[line] === '' && values.length === 1 ? '（空输出）' : ''}</span>{differs && <small>不同</small>}</span>;
    })}</pre>;
    return <details className="wb-case" key={`${index}-${name}`} open={index === 0 || failed}>
      <summary><strong>{name}</strong><Verdict submission={{ verdict: item.verdict === 'AC' ? 'SAMPLE_PASS' : item.verdict, finishedAt: true, mode: 'run' }} />{item.timeMs != null && <span>{elapsedText(item.timeMs)}</span>}</summary>
      {item.message && <p className="wb-result-message">{item.message}</p>}
      <div className={`wb-case-outputs${known ? '' : ' wb-case-custom'}`}>
        {known ? <div><span>预期输出</span>{renderOutput(expected, actual, '预期输出')}</div> : <p className="wb-result-message">自定义输入没有预期答案，仅检查程序是否正常运行。</p>}
        <div><span>实际输出</span>{renderOutput(actual, expected, '实际输出')}</div>
      </div>
      <details className="wb-case-input"><summary>查看输入</summary><pre tabIndex={0}>{item.input || '（空输入）'}</pre></details>
      {item.exitCode != null && item.exitCode !== 0 && <p className="wb-result-message">退出码：{item.exitCode}</p>}
    </details>;
  })}</div>;
}

export default function Workbench({shortcuts={}, problemId, preparedProblem=null, contest = null, reviewTask = null, api, onProgress, onExit, onSolution, solutionOpen=false, onNext, headerStart, headerEnd }) {
  const contestId = contest?.id || null;
  const runningContest = contest?.status === 'running';
  const endedContest = Boolean(contest && !runningContest);
  const reviewId = contestId ? null : reviewTask?.id;
  const contextKey = draftKey(problemId, reviewId ? `review:${reviewId}` : contestId);
  const apiRef = useRef(api);
  const callbacks = useRef({ onProgress, onExit, onSolution, onNext });
  apiRef.current = api;
  callbacks.current = { onProgress, onExit, onSolution, onNext };

  const activeRecord = useRef(null);
  const sectionRef = useRef(null);
  const statementRef = useRef(null);
  const editorRef = useRef(null);
  const consoleButtonRef = useRef(null);
  const undoReplace = useRef(null);
  const officialRef = useRef(null);
  const officialReported = useRef(new Set());
  const [problem, setProblem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [code, setCode] = useState('');
  const [codeLanguage,setCodeLanguage]=useState('cpp17');
  const [saveState, setSaveState] = useState({ kind: 'automatic' });
  const [pane, setPane] = useState('both');
  const [cursor, setCursor] = useState({ line: 1, column: 1 });
  const [submissions, setSubmissions] = useState([]);
  const [resultId, setResultId] = useState(null);
  const [creating, setCreating] = useState(false);
  const [actionError, setActionError] = useState('');
  const [pollError, setPollError] = useState('');
  const [consoleOpen, setConsoleOpen] = useState(false);
  const [consoleTab, setConsoleTab] = useState('input');
  const [sample, setSample] = useState('custom');
  const [input, setInput] = useState('');
  const [restoreAvailable, setRestoreAvailable] = useState(false);
  const [localDraftRecovery, setLocalDraftRecovery] = useState(null);
  const [outputTab, setOutputTab] = useState('output');
  const [copied, setCopied] = useState(false);
  const [openingOfficial, setOpeningOfficial] = useState(false);
  const [officialSession, setOfficialSession] = useState(null);
  const [officialPollError, setOfficialPollError] = useState('');
  const [language, setLanguage] = useState('original');
  const [translation, setTranslation] = useState(null);
  const [translationBusy, setTranslationBusy] = useState(false);
  const [translationError, setTranslationError] = useState('');
  const [statementFontSize, setStatementFontSize] = useState(readStatementFontSize);
  const changeStatementFontSize = size => {
    if (!Number.isInteger(size) || size < 14 || size > 32) return;
    setStatementFontSize(size);
    try { localStorage.setItem(STATEMENT_FONT_KEY, String(size)); } catch { /* Keep the in-session choice. */ }
  };

  const isActive = record => activeRecord.current === record;
  const saveRecord = useCallback(record => {
    if (!record?.loaded || record.closed || record.version <= record.savedVersion) return Promise.resolve(true);
    if (byteLength(record.code) > MAX_BYTES) {
      if (isActive(record)) setSaveState({ kind: 'error', retained: record.retained, message: '代码超过 64 KiB，请缩短后保存。' });
      return Promise.resolve(false);
    }
    if (record.saving) return record.saving;
    record.saving = (async () => {
      while (record.version > record.savedVersion && !record.closed) {
        const version = record.version;
        const snapshot = record.code;
        const revision = record.revision;
        if (byteLength(snapshot) > MAX_BYTES) {
          if (isActive(record)) setSaveState({ kind: 'error', retained: record.retained, message: '代码超过 64 KiB，请缩短后保存。' });
          return false;
        }
        if (isActive(record)) setSaveState({ kind: 'saving' });
        try {
          const answer = await queuedSave(record.key, requestBody(record, { code: snapshot }), apiRef.current, revision);
          record.savedVersion = version;
          if (!answer.skipped) markDraftSaved(record, version);
          if (isActive(record)) setSaveState({
            kind: record.version > version ? 'unsaved' : 'saved', savedAt: answer.savedAt,
          });
        } catch (error) {
          if (isActive(record)) setSaveState({ kind: 'error', retained: record.retained, message: error.message || '草稿保存失败' });
          return false;
        }
      }
      return true;
    })().finally(() => { record.saving = null; });
    return record.saving;
  }, []);

  useEffect(() => {
    let alive = true;
    const record = {
      key: contextKey, id: problemId, contestId, reviewId, owner: `${Date.now()}-${Math.random()}`,
      code: '', version: 0, savedVersion: 0, loaded: false, closed: endedContest,
      timer: null, saving: null,
    };
    activeRecord.current = record;
    undoReplace.current = null;
    setProblem(null);
    setLoading(true);
    setLoadError('');
    setCode('');
    setSubmissions([]);
    setResultId(null);
    setCreating(false);
    setActionError('');
    setPollError('');
    setSaveState({ kind: 'automatic' });
    setCursor({ line: 1, column: 1 });
    setRestoreAvailable(false);
    setLocalDraftRecovery(null);
    setConsoleOpen(false);
    setConsoleTab('input');
    setOutputTab('output');
    setCopied(false);
    setOpeningOfficial(false);
    setOfficialSession(null);
    setOfficialPollError('');
    setLanguage('original');
    setTranslation(null);
    setTranslationBusy(false);
    setTranslationError('');
    setSample('custom');
    setInput('');
    (async () => {
      try {
        const prefetched = !loadAttempt && !contestId && !reviewId && preparedProblem ? await preparedProblem : null;
        const answer = prefetched || await apiRef.current(`${queryPath('problem', problemId, contestId, reviewId)}&background=1${loadAttempt ? '&refresh=1' : ''}`);
        if (!alive || !isActive(record)) return;
        const backup = readDraft(record.key);
        record.locked = Boolean(answer.locked && !contestId);
        record.closed = record.closed || record.locked;
        const useLocal = backup?.dirty && (!answer.draftSavedAt || Number(backup.modifiedAt || 0) >= Date.parse(answer.draftSavedAt));
        record.language = useLocal ? backup.language || 'cpp17' : answer.draftLanguage || 'cpp17';
        setCodeLanguage(record.language);
        record.code = useLocal ? backup.code : (answer.draftSavedAt ? answer.draft : (answer.draft || (record.language==='python3' ? PYTHON_TEMPLATE : TEMPLATE)));
        if (backup?.dirty && !useLocal && backup.code !== record.code) {
          // A newer draft restored from another computer wins. Keep this
          // device's unsent version separately, never silently overwrite it.
          try { localStorage.setItem(`${record.key}.recovery.${backup.modifiedAt || Date.now()}`, JSON.stringify(backup)); } catch { /* The original backup is still present. */ }
          setLocalDraftRecovery(backup.code);
        }
        record.loaded = true;
        record.revision = latestDraftRevision.get(record.key) || 0;
        if (useLocal) {
          record.version = 1;
          touchDraft(record);
        }
        setCode(record.code);
        setProblem(answer);
        const prepared=(answer.translation?.targetLanguage==='zh-CN'||answer.translation?.kind==='site') && answer.translation.markdown ? answer.translation : null;
        setTranslation(prepared);
        setLanguage(prepared ? 'zh' : 'original');
        const history = (answer.submissions || []).slice().sort((a, b) => String(b.submittedAt || '').localeCompare(String(a.submittedAt || '')));
        setSubmissions(history);
        setResultId(history[0]?.id || null);
        const first = answer.samples?.[0];
        setSample(first ? 'samples' : 'custom');
        setInput('');
        setLoading(false);
        setSaveState({ kind: record.closed ? 'closed' : useLocal ? 'unsaved' : answer.draftSavedAt || answer.draft ? 'saved' : 'automatic' });
        if (useLocal && !record.closed) record.timer = setTimeout(() => saveRecord(record), 850);
        requestAnimationFrame(() => {
          if (!isActive(record)) return;
          if (statementRef.current) statementRef.current.scrollTop = 0;
          if (editorRef.current) editorRef.current.scrollTop = 0;
          if (document.activeElement === document.body) statementRef.current?.focus();
        });
      } catch (error) {
        if (alive && isActive(record)) {
          setLoading(false);
          setLoadError(error.message || '题目载入失败');
        }
      }
    })();
    return () => {
      alive = false;
      clearTimeout(record.timer);
      saveRecord(record);
      if (officialRef.current?.record === record) {
        const session = officialRef.current;
        officialRef.current = null;
        apiRef.current('official/close', { sessionId: session.id }).catch(() => undefined);
      }
      if (isActive(record)) activeRecord.current = null;
    };
    // api and callback references may change with workspace polling. A draft
    // belongs to its identity, so those renders must not reload the editor.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contextKey, problemId, contestId, reviewId, loadAttempt, saveRecord]);

  useEffect(() => {
    if (!problem?.statementLoading) return;
    let alive = true, timer;
    const record = activeRecord.current;
    const poll = async () => {
      try {
        const answer = await apiRef.current(`${queryPath('problem', problemId, contestId, reviewId)}&background=1`);
        if (!alive || !isActive(record)) return;
        // A late statement response must never reset an editor or its draft.
        setProblem(answer);
        if (answer.statementLoading) timer = setTimeout(poll, 500);
      } catch (error) {
        if (alive && isActive(record)) setProblem(previous => ({ ...previous, statementLoading: false, statementError: error.message }));
      }
    };
    timer = setTimeout(poll, 450);
    return () => { alive = false; clearTimeout(timer); };
  }, [problemId, contestId, reviewId, problem?.statementLoading]);

  async function retryStatement() {
    const record = activeRecord.current;
    if (!record?.loaded) return;
    setProblem(previous => ({ ...previous, statementLoading: true, statementError: '' }));
    try {
      const answer = await apiRef.current(`${queryPath('problem', record.id, record.contestId, record.reviewId)}&background=1&refresh=1`);
      if (isActive(record)) setProblem(answer);
    } catch (error) {
      if (isActive(record)) setProblem(previous => ({ ...previous, statementLoading: false, statementError: error.message }));
    }
  }

  useEffect(() => {
    const record = activeRecord.current;
    if (!record || record.key !== contextKey) return;
    record.closed = endedContest || Boolean(record.locked);
    if (record.closed) {
      clearTimeout(record.timer);
      setSaveState({ kind: 'closed' });
    }
  }, [endedContest, contextKey]);

  const pending = submissions.find(submissionPending) || null;
  const result = submissions.find(row => row.id === resultId) || submissions[0] || null;
  useEffect(() => {
    if (result?.stderr && !result.output && result.finishedAt) setOutputTab('stderr');
  }, [result?.id, result?.finishedAt, result?.stderr]);
  const sidePracticeLocked = Boolean(problem?.locked && !runningContest);
  const unavailable = loading || !problem || endedContest || sidePracticeLocked || activeRecord.current?.key !== contextKey;
  const busy = creating || Boolean(pending);
  const officialBusy = openingOfficial || ['loading', 'submitted', 'judging'].includes(officialSession?.status);
  const samples = problem?.samples || [];
  const slot = contest?.slots?.find(row => row.id === problemId);

  const announceCompletion = useCallback(async answer => {
    const submission = answer.submission;
    if (!submission?.finishedAt || submission.mode !== 'submit') return;
    try {
      const workspace = answer.workspace || await apiRef.current('workspace');
      callbacks.current.onProgress?.(workspace);
    } catch { /* The parent also refreshes the workspace; keep the verdict visible. */ }
  }, []);

  useEffect(() => {
    const receive = event => {
      const submission = event.detail?.submission, record = activeRecord.current;
      if (!submission || !record || submission.problemId !== record.id || (submission.contestId || null) !== record.contestId) return;
      // A very fast result can precede the HTTP response assigning its ID.
      if (record.localEvents && record.localEvents.size < 16) record.localEvents.set(submission.id, submission);
      setSubmissions(rows => rows.some(row => row.id === submission.id) ? mergeSubmission(rows, submission) : rows);
      if (submission.finishedAt && submission.id === record.localSubmissionId) announceCompletion({submission});
    };
    window.addEventListener('tb:submission-status', receive);
    return () => window.removeEventListener('tb:submission-status', receive);
  }, [announceCompletion]);

  useEffect(() => {
    if (!pending) return;
    let alive = true;
    let timer;
    const record = activeRecord.current;
    const poll = async () => {
      try {
        const answer = await apiRef.current(`submission?id=${encodeURIComponent(pending.id)}`);
        if (!alive || !isActive(record)) return;
        setPollError('');
        setSubmissions(rows => mergeSubmission(rows, answer.submission));
        if (answer.submission.finishedAt) {
          await announceCompletion(answer);
        } else timer = setTimeout(poll, 650);
      } catch (error) {
        if (alive && isActive(record)) {
          setPollError(error.message || '暂时无法取得评测结果，正在重试');
          timer = setTimeout(poll, 1800);
        }
      }
    };
    timer = setTimeout(poll, 200);
    return () => { alive = false; clearTimeout(timer); };
  }, [pending?.id, contextKey, announceCompletion]);

  const announceOfficialCompletion = useCallback(async (session, record) => {
    if (session.status !== 'finished' || !session.verdict || !session.submissionId || officialReported.current.has(session.sessionId)) return;
    officialReported.current.add(session.sessionId);
    if (session.verdict === 'AC') playAcceptedSound(`${session.platform || record.id}:${session.submissionId}`);
    if (session.submission && isActive(record)) {
      setSubmissions(rows => mergeSubmission(rows, session.submission));
      setResultId(session.submission.id);
      setConsoleOpen(true); setConsoleTab('result');
    }
    // Refresh progress independently; displaying the persisted receipt never
    // waits for a full workspace/statement round trip.
    apiRef.current('workspace').then(workspace => {
      if (isActive(record)) callbacks.current.onProgress?.(workspace);
    }).catch(() => undefined);
    if (session.submission) return;
    try {
      // 官方回执已入库，但当前工作台的提交历史/结果栏还是旧的——拉回本题记录并合并，
      // 让官方 AC 当场出现在历史里，不必退出重进。
      if (isActive(record)) {
        const answer = await apiRef.current(`${queryPath('problem', record.id, record.contestId, record.reviewId)}&background=1`);
        if (isActive(record) && Array.isArray(answer?.submissions)) {
          const history = answer.submissions.slice().sort((a, b) => String(b.submittedAt || '').localeCompare(String(a.submittedAt || '')));
          setSubmissions(history);
          const official = history.find(row => row.scope === 'official' && row.message?.includes(`#${session.submissionId}`)) || history.find(row => row.scope === 'official');
          if (official) setResultId(official.id);
          setConsoleOpen(true); setConsoleTab('result');
        }
      }
    } catch { /* Keep the genuine official receipt visible if a refresh fails. */ }
  }, []);

  useEffect(() => {
    const receive = event => {
      const session = event.detail, current = officialRef.current;
      if (!session || !current || current.id !== session.sessionId || !isActive(current.record)) return;
      current.pushed = (current.pushed || 0) + 1;
      current.status = session.status;
      setOfficialSession(session);
      setOfficialPollError('');
      announceOfficialCompletion(session, current.record);
    };
    window.addEventListener('tb:official-status', receive);
    return () => window.removeEventListener('tb:official-status', receive);
  }, [announceOfficialCompletion]);

  useEffect(() => {
    if (!officialSession?.sessionId || OFFICIAL_TERMINAL.has(officialSession.status)) return;
    let alive = true, timer;
    const record = activeRecord.current, sessionId = officialSession.sessionId;
    const poll = async () => {
      const pushed = officialRef.current?.pushed || 0;
      try {
        const answer = await apiRef.current(`official/status?sessionId=${encodeURIComponent(sessionId)}`);
        if (!alive || !isActive(record) || officialRef.current?.id !== sessionId) return;
        if ((officialRef.current.pushed || 0) !== pushed) {
          if (!OFFICIAL_TERMINAL.has(officialRef.current.status)) timer = setTimeout(poll, 900);
          return;
        }
        officialRef.current.status = answer.status;
        setOfficialSession({ ...answer, sessionId });
        setOfficialPollError('');
        await announceOfficialCompletion({ ...answer, sessionId }, record);
        if (!OFFICIAL_TERMINAL.has(answer.status)) timer = setTimeout(poll, ['needs_login', 'needs_verification', 'ready'].includes(answer.status) ? 2200 : 900);
      } catch (error) {
        if (alive && isActive(record)) {
          setOfficialPollError(error.message || '暂时无法读取原站状态，正在重试。');
          timer = setTimeout(poll, 2500);
        }
      }
    };
    timer = setTimeout(poll, 450);
    return () => { alive = false; clearTimeout(timer); };
  }, [officialSession?.sessionId, contextKey, announceOfficialCompletion]);

  useEffect(()=>{
    if(officialSession?.status!=='finished'||!officialSession.sessionId)return;
    // This effect runs after React commits the result to the visible workbench.
    let cancelled=false,timer;
    const acknowledge=async(attempt=0)=>{try{const result=await apiRef.current('official/ack',{sessionId:officialSession.sessionId});if(!cancelled&&!result.closed&&attempt<4)timer=setTimeout(()=>acknowledge(attempt+1),700);}catch{if(!cancelled&&attempt<4)timer=setTimeout(()=>acknowledge(attempt+1),1000);}};
    if (!officialSession.submission && !submissions.some(row => row.scope === 'official' && row.message?.includes(`#${officialSession.submissionId}`))) return;
    const frame=requestAnimationFrame(()=>acknowledge());
    return()=>{cancelled=true;cancelAnimationFrame(frame);clearTimeout(timer);};
  },[officialSession?.sessionId,officialSession?.status,officialSession?.submission,submissions]);
  const updateCode = useCallback(value => {
    const record = activeRecord.current;
    if (!record?.loaded || record.closed) return;
    record.code = value;
    record.version += 1;
    touchDraft(record);
    retainDraft(record);
    setCode(value);
    setSaveState({ kind: 'unsaved' });
    clearTimeout(record.timer);
    record.timer = setTimeout(() => saveRecord(record), 850);
  }, [saveRecord]);

  useEffect(() => {
    const beforeUpdate = event => {
      const record = activeRecord.current;
      clearTimeout(record?.timer);
      event.detail.waitUntil(record && !record.loaded ? Promise.resolve(false) : saveRecord(record));
    };
    window.addEventListener('tb-before-update', beforeUpdate);
    return () => window.removeEventListener('tb-before-update', beforeUpdate);
  }, [saveRecord]);

  const changeCodeLanguage = event => {
    const record=activeRecord.current;if(!record?.loaded||record.closed)return;
    const next=event.target.value;if(next===record.language)return;
    const newTemplate=next==='python3' ? PYTHON_TEMPLATE : TEMPLATE;
    // Each language keeps an independent editor buffer for this problem.
    try {localStorage.setItem(`${record.key}.language.${record.language||'cpp17'}`,record.code);}catch{}
    let remembered;try{remembered=localStorage.getItem(`${record.key}.language.${next}`);}catch{}
    record.language=next;setCodeLanguage(next);
    updateCode(remembered ?? newTemplate);
  };
  const manualSave = () => {
    const record = activeRecord.current;
    if (!record?.loaded || record.closed || sidePracticeLocked) return;
    if (record.version <= record.savedVersion) {
      record.version += 1;
      touchDraft(record);
      retainDraft(record);
    }
    clearTimeout(record.timer);
    saveRecord(record);
  };
  const execute = async mode => {
    const record = activeRecord.current;
    if (!record?.loaded || unavailable || busy) return;
    if (!record.code.trim()) {
      setActionError('先写入 C++ 代码，再运行或提交。');
      editorRef.current?.focus();
      return;
    }
    if (byteLength(record.code) > MAX_BYTES || (mode === 'run' && sample === 'custom' && byteLength(input) > MAX_BYTES)) {
      setActionError(byteLength(record.code) > MAX_BYTES ? '代码超过 64 KiB，请缩短后再提交。' : '标准输入超过 64 KiB，请缩短测试数据。');
      return;
    }
    setCreating(true);
    record.localEvents = new Map();
    setActionError('');
    setConsoleOpen(true);
    setConsoleTab('result');
    setOutputTab('output');
    clearTimeout(record.timer);
    saveRecord(record);
    try {
      const answer = await apiRef.current('submissions', requestBody(record, {
        code: record.code, mode, ...(mode === 'run' ? { input: sample === 'custom' ? input : '', sampleRun: sample !== 'custom' } : {}),
      }));
      if (!isActive(record)) return;
      record.localSubmissionId = answer.submission.id;
      const latest = record.localEvents?.get(answer.submission.id);
      if (latest) answer.submission = latest;
      setSubmissions(rows => mergeSubmission(rows, answer.submission));
      setResultId(answer.submission.id);
      await announceCompletion(answer);
    } catch (error) {
      if (isActive(record)) setActionError(error.message || '未能开始评测，请重试。');
    } finally {
      record.localEvents = null;
      if (isActive(record)) setCreating(false);
    }
  };
  const focusPane = next => {
    setPane(next);
    requestAnimationFrame(() => (next === 'statement' ? statementRef.current : editorRef.current)?.focus());
  };
  const openOfficial = async (path = 'official/submit') => {
    const record = activeRecord.current;
    if (!record?.loaded || unavailable || sidePracticeLocked || record.officialBusy || (path === 'official/submit' && officialBusy)) return;
    if (!record.code.trim() || byteLength(record.code) > MAX_BYTES) {
      setActionError(!record.code.trim() ? '先写入代码，再提交到原站。' : '代码超过 64 KiB，请缩短后再提交。');
      return;
    }
    if (path === 'official/submit') primeAcceptedSound();
    record.officialBusy = true;
    setOpeningOfficial(true); setActionError(''); setOfficialPollError('');
    setConsoleOpen(true); setConsoleTab('result');
    saveRecord(record);
    try {
      const answer = await apiRef.current(path, requestBody(record, { code: record.code }));
      if (!answer.sessionId) throw new Error('原站面板未返回会话，请重试。');
      if (!isActive(record)) {
        apiRef.current('official/close', { sessionId: answer.sessionId }).catch(() => undefined);
        return;
      }
      officialRef.current = { id: answer.sessionId, record, status: answer.status };
      setOfficialSession(answer);
      await announceOfficialCompletion(answer, record);
    } catch (error) {
      if (isActive(record)) {
        setActionError(error.message || '暂时无法提交到原站，请稍后重试。');
      }
    } finally { record.officialBusy = false; if (isActive(record)) setOpeningOfficial(false); }
  };
  const closeOfficial = async () => {
    const session = officialRef.current;
    if (!session || openingOfficial) return;
    setOpeningOfficial(true);
    try {
      const answer = await apiRef.current('official/close', { sessionId: session.id });
      if (isActive(session.record) && officialRef.current?.id === session.id) {
        setOfficialSession({ ...answer, sessionId: session.id });
        setOfficialPollError('');
        editorRef.current?.focus();
      }
    } catch (error) { if (isActive(session.record)) setOfficialPollError(error.message || '暂时无法关闭原站面板。'); }
    finally { if (isActive(session.record)) setOpeningOfficial(false); }
  };
  const translateStatement = async () => {
    const record = activeRecord.current;
    if (!record?.loaded || loading || !problem?.markdown) return;
    setLanguage('zh');
    if (translation || record.translationBusy) return;
    record.translationBusy = true;
    setTranslationBusy(true); setTranslationError('');
    try {
      const answer = await apiRef.current('problem/translate', requestBody(record));
      if (!isActive(record)) return;
      if (!answer.markdown || answer.targetLanguage !== 'zh-CN') throw new Error('翻译服务未返回中文题面，已保留原文。');
      setTranslation(answer);
    } catch (error) {
      if (isActive(record)) { setTranslationError(error.message || '暂时无法翻译，已保留原文。'); setLanguage('original'); }
    } finally { record.translationBusy = false; if (isActive(record)) setTranslationBusy(false); }
  };
  const editorCommand = command => {
    if (command === 'official') openOfficial();
    else if (command === 'submit') openOfficial();
    else if (command === 'run') execute('run');
    else if (command === 'save') manualSave();
    else if (command === 'pane-0') setPane('both');
    else if (command === 'pane-1') focusPane('statement');
    else if (command === 'pane-2') focusPane('code');
  };
  const handleKeys = event => {
    if (event.defaultPrevented || event.nativeEvent.isComposing) return;
    const id=['official','submit','run','save','pane-0','pane-1','pane-2'].find(id=>matchesShortcut(event,id,shortcuts));
    if(id){event.preventDefault();event.stopPropagation();editorCommand(id);}

  };
  const loadOwnCode = value => {
    if (unavailable || typeof value !== 'string') return;
    undoReplace.current = activeRecord.current.code;
    setRestoreAvailable(true);
    updateCode(value);
    if (pane === 'statement') setPane('both');
    requestAnimationFrame(() => editorRef.current?.focus());
  };
  const selectSample = event => {
    setSample(event.target.value);
  };
  const selectConsole = tab => {
    if (consoleOpen && consoleTab === tab) setConsoleOpen(false);
    else { setConsoleTab(tab); setConsoleOpen(true); }
  };
  const copyOutput = async () => {
    try {
      await navigator.clipboard.writeText(result?.[outputTab] || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { setActionError('暂时无法复制，可以选中输出后按 Ctrl+C。'); }
  };
  const exit = () => { saveRecord(activeRecord.current); callbacks.current.onExit?.(); };
  const saveLabel = saveState.kind === 'saving' ? '保存中…' : saveState.kind === 'unsaved' ? '等待保存'
    : saveState.kind === 'error' ? (saveState.retained ? '保存失败 · 本机草稿已保留' : '草稿保存失败')
    : saveState.kind === 'closed' ? (endedContest ? '本场已结束' : '考场题目')
    : saveState.kind === 'automatic' ? '自动保存' : '草稿已保存';

  return <section className={`tb-workbench wb-pane-${pane}`} ref={sectionRef} onKeyDown={handleKeys} aria-label="代码训练工作台" data-problem-id={problemId}>

    {sidePracticeLocked && !endedContest && <div className="wb-notice">这题正在模拟赛中，请进入考场运行与提交。</div>}
    {actionError && <div className="wb-error-strip" role="alert"><span>{actionError}</span><button type="button" onClick={() => setActionError('')}>知道了</button></div>}

    <div className="wb-body">
      <div className="wb-statement-pane">
        <div className="wb-pane-header wb-merged-header"><div className="wb-toolbar">
      <button type="button" className="wb-icon-button" onClick={exit} title={runningContest ? '返回工作台（比赛继续计时）' : '返回列表'} aria-label={runningContest ? '返回工作台' : '返回列表'}><ArrowLeft size={17} /></button>
      {headerStart}
      <div className="wb-heading">
        {slot && !headerStart && <span className="wb-letter">{slot.letter}</span>}
        <strong title={problem?.title}><InlineTitle>{problem?.title || (loading ? '载入题目…' : '题目')}</InlineTitle></strong>
        {problem && <span className="wb-limits">{elapsedText(problem.limits?.timeMs)} · {problem.limits?.memoryMb || '—'} MB</span>}
      </div>
      <div className="wb-pane-buttons" role="group" aria-label="工作台布局">
        <button type="button" className="wb-icon-button" aria-pressed={pane === 'statement'} onClick={() => focusPane('statement')} title="只看题面 · Alt+1" aria-label="只看题面"><PanelLeft size={16} /></button>
        <button type="button" className="wb-icon-button" aria-pressed={pane === 'both'} onClick={() => setPane('both')} title="题面与代码 · Alt+0" aria-label="题面与代码"><PanelsTopLeft size={16} /></button>
        <button type="button" className="wb-icon-button" aria-pressed={pane === 'code'} onClick={() => focusPane('code')} title="只看代码 · Alt+2" aria-label="只看代码"><Code2 size={16} /></button>
      </div>
    </div><div className="wb-statement-actions">
          <div className="wb-font-controls" role="group" aria-label="题面字号调节">
            <button type="button" aria-label="缩小题面字号" title="缩小题面字号" disabled={statementFontSize <= 14} onClick={() => changeStatementFontSize(Math.max(14,statementFontSize - 1))}>A−</button>
            <BoundedNumber aria-label="题面字号" min={14} max={32} unit="px" value={statementFontSize} required onChange={event => changeStatementFontSize(Number(event.target.value))}/>
            <button type="button" aria-label="放大题面字号" title="放大题面字号" disabled={statementFontSize >= 32} onClick={() => changeStatementFontSize(Math.min(32,statementFontSize + 1))}>A+</button>
          </div>
          <div className="wb-language-toggle" role="group" aria-label="题面语言"><button type="button" aria-pressed={language === 'original'} onClick={() => { setLanguage('original'); setTranslationError(''); }}>原文</button><button type="button" aria-pressed={language === 'zh'} disabled={loading || !problem?.markdown || translationBusy} onClick={translateStatement}>{translationBusy ? '翻译中…' : '中文'}</button></div>
          {problem?.url && <a href={problem.url} target="_blank" rel="noreferrer" title="在浏览器打开原题">原题<ExternalLink size={12} /></a>}
        </div></div>
        {translationBusy && <p className="wb-translation-note" role="status"><LoaderCircle size={12} className="wb-spinner" />正在翻译公开题面，原文仍可阅读。</p>}
        {translationError && <div className="wb-translation-note wb-translation-error" role="alert"><span>{translationError}</span><button type="button" onClick={translateStatement}>重试</button></div>}
        <article className="wb-statement" ref={statementRef} tabIndex={0} aria-label="题面内容" style={{ '--statement-font-size': `${statementFontSize}px` }}>
          {loading ? <div className="wb-empty"><LoaderCircle className="wb-spinner" size={22} /><span>正在载入题面</span></div>
            : loadError ? <div className="wb-empty"><span>{loadError}</span><button type="button" className="wb-button" onClick={() => setLoadAttempt(value => value + 1)}><RotateCcw size={14} />重新载入</button></div>
            : problem?.markdown ? <StatementMarkdown markdown={language === 'zh' && translation ? translation.markdown : problem.markdown} samples={problem.samples} title={problem.title} images={problem.images} />
            : problem?.statementLoading ? <div className="wb-empty" role="status"><LoaderCircle className="wb-spinner" size={22}/><strong>正在读取原站题面</strong>{problem?.url && <a className="wb-button" href={problem.url} target="_blank" rel="noreferrer">打开原题<ExternalLink size={14}/></a>}</div>
            : <div className="wb-empty"><BookOpen size={24} /><strong>题面暂时未能加载</strong><span>{problem?.statementError || '请重试读取原站题面。'}</span><button type="button" className="wb-button" onClick={retryStatement}><RotateCcw size={14} />重新载入</button>{problem?.url && <a className="wb-button" href={problem.url} target="_blank" rel="noreferrer">打开原题<ExternalLink size={14} /></a>}</div>}
        </article>
      </div>

      <div className="wb-code-pane">
        <div className="wb-pane-header wb-editor-header">
          <span><Code2 size={14}/><ThemedSelect aria-label="编程语言" value={codeLanguage} disabled={unavailable||busy||officialBusy} onChange={changeCodeLanguage}><option value="cpp17">C++17</option><option value="python3">Python 3</option></ThemedSelect></span>
          <span className={`wb-save-state wb-save-${saveState.kind}`} title={saveState.message || '草稿自动保存；Ctrl+S 立即保存'} aria-live="polite">{saveState.kind === 'saving' ? <LoaderCircle size={11} className="wb-spinner" /> : saveState.kind === 'saved' ? <Check size={11} /> : null}{saveLabel}</span>
          <div className="wb-editor-actions">
            {onSolution && !runningContest && !problem?.locked && <button type="button" className="wb-button wb-solution-button" aria-pressed={solutionOpen} disabled={!problem} onClick={() => callbacks.current.onSolution?.(problemId)}><BookOpen size={14} />题解</button>}
            {onNext && <button type="button" className="wb-button wb-next-button" onClick={async () => { if(await saveRecord(activeRecord.current)) callbacks.current.onNext?.(); }}>下一题<ArrowRight size={14} /></button>}
            {localDraftRecovery !== null && <button type="button" className="wb-button" disabled={unavailable} title="当前为更新的同步版本；可恢复本机未上传的旧草稿" onClick={() => {
              undoReplace.current = code;
              updateCode(localDraftRecovery);
              setLocalDraftRecovery(null);
              setRestoreAvailable(true);
            }}><History size={14}/>恢复本机草稿</button>}
            {restoreAvailable && <button type="button" className="wb-icon-button" disabled={unavailable} aria-label="撤销载入代码" title="撤销载入代码" onClick={() => {
              const previous = undoReplace.current;
              undoReplace.current = null;
              setRestoreAvailable(false);
              if (typeof previous === 'string') updateCode(previous);
            }}><RotateCcw size={14} /></button>}
          </div>
          {headerEnd&&<div className="wb-context-actions">{headerEnd}</div>}
        </div>
        <div className="wb-editor">
          <CodeEditor shortcuts={shortcuts} ref={editorRef} value={code} docKey={contextKey} onChange={updateCode} onCursorChange={setCursor} onCommand={editorCommand} onLeave={() => consoleButtonRef.current?.focus()} readOnly={unavailable} disabled={loading || !problem} language={codeLanguage} ariaLabel={codeLanguage==='python3'?'Python 代码':'C++ 代码'} />
        </div>
        <div className="wb-editor-status"><span>Ln {cursor.line}, Col {cursor.column}</span><span title="Tab 缩进，Shift+Tab 取消缩进，Ctrl+Tab 离开编辑器">Tab 缩进 · Ctrl+Tab 离开</span></div>
        <div className="wb-run-toolbar">
          <ThemedSelect value={sample} onChange={selectSample} aria-label="运行输入" disabled={loading || !problem}>
            {samples.length > 0 && <option value="samples">全部样例（{samples.length}）</option>}
            <option value="custom">自定义输入</option>
          </ThemedSelect>
          <span className={`wb-scope wb-scope-${problem?.judge?.scope || 'samples'}`} title={problem?.judge?.scope === 'local' ? `本地验证用例 ${problem.judge.cases || 0} 个` : '仅使用公开样例，通过样例不会计入已 AC'}>{problem?.judge?.label || (problem?.judge?.scope === 'local' ? '本地验证' : '样例评测')}</span>
          <div className="wb-run-actions">
            <button type="button" className="wb-button" disabled={unavailable || busy} onClick={() => execute('run')} title={sample === 'samples' ? '编译并对比全部官方样例 · Ctrl+R' : '编译并运行自定义输入 · Ctrl+R'}><Play size={14} />{sample === 'custom' ? '运行输入' : '运行样例'}</button>
            <button type="button" className="wb-button wb-primary" disabled={unavailable || officialBusy} onClick={() => openOfficial()} title="原站提交 · Ctrl+Enter">{officialBusy ? <LoaderCircle size={14} className="wb-spinner" /> : <Send size={14} />}提交</button>
          </div>
        </div>
        <div className="wb-console-tabs" role="group" aria-label="输入与评测记录">
          <button type="button" ref={consoleButtonRef} aria-pressed={consoleOpen && consoleTab === 'input'} onClick={() => selectConsole('input')}><Terminal size={13} />输入与样例</button>
          <button type="button" aria-pressed={consoleOpen && consoleTab === 'result'} onClick={() => selectConsole('result')}><Play size={12} />运行结果{pending && <span className="wb-pending-dot" />}</button>
          <button type="button" aria-pressed={consoleOpen && consoleTab === 'history'} onClick={() => selectConsole('history')}><History size={13} />记录<span className="wb-count">{submissions.filter(row => row.mode === 'submit').length}</span></button>
          <button type="button" className="wb-console-toggle" onClick={() => setConsoleOpen(value => !value)} aria-label={consoleOpen ? '收起控制台' : '展开控制台'} aria-expanded={consoleOpen}>{consoleOpen ? <ChevronDown size={15} /> : <ChevronUp size={15} />}</button>
        </div>
        {consoleOpen && <div className={`wb-console wb-console-${consoleTab}`}>
          {consoleTab === 'input' ? sample === 'samples' ? <div className="wb-sample-list">{samples.map((item, index) => <details key={index} open={index === 0}><summary>{item.name || `样例 ${index + 1}`}</summary><div className="wb-case-outputs"><div><span>样例输入</span><pre tabIndex={0}>{item.input || '（空输入）'}</pre></div><div><span>预期输出</span><pre tabIndex={0}>{item.output || '（空输出）'}</pre></div></div></details>)}<p className="wb-result-message">运行会对比全部样例；通过样例不会计入已 AC。</p></div> : <div className="wb-input-grid">
            <label><span>标准输入</span><textarea value={input} onChange={event => { setInput(event.target.value); setSample('custom'); }} aria-label="标准输入" spellCheck={false} placeholder="输入测试数据；Ctrl+R 编译运行" /></label>
          </div> : consoleTab === 'history' ? <div className="wb-history">
            {submissions.length ? submissions.map(row => <div className={`wb-history-row${row.id === resultId ? ' wb-history-selected' : ''}`} key={row.id}>
              <button type="button" className="wb-history-main" onClick={() => { setResultId(row.id); setConsoleTab('result'); setOutputTab(row.stderr && !row.output ? 'stderr' : 'output'); }}>
                <span className="wb-history-kind">{row.mode === 'run' ? '运行' : '提交'}</span><Verdict submission={row} /><time dateTime={row.submittedAt}>{dateText(row.submittedAt)}</time>
              </button>
              <button type="button" className="wb-history-load" disabled={unavailable || !row.code} onClick={() => loadOwnCode(row.code)} title="将这次自己的代码载入编辑器">载入代码</button>
            </div>) : <div className="wb-empty"><History size={21} /><span>运行或提交后，记录会保存在这里。</span></div>}
          </div> : <div className="wb-result">
            {officialSession && !['finished', 'closed'].includes(officialSession.status) && <div className="wb-official-status" aria-label="原站提交状态">
              <div role="status"><strong>{OFFICIAL_STATES[officialSession.status] || '原站提交'}</strong><span>{officialSession.message}</span></div>
              {['needs_browser', 'needs_login', 'needs_verification', 'unconfirmed', 'error'].includes(officialSession.status) && <button type="button" className="wb-button" disabled={unavailable || openingOfficial} onClick={() => openOfficial('official/open')}>{officialSession.status === 'needs_verification' ? '完成原站验证' : '在浏览器查看'}</button>}
              {officialPollError && <p className="wb-poll-error" role="alert">{officialPollError}</p>}
            </div>}
            {creating && !pending ? <div className="wb-empty"><LoaderCircle size={20} className="wb-spinner" /><span>正在开始评测</span></div> : result ? <>
              <div className="wb-result-summary" aria-live="polite"><Verdict submission={result} />
                {result.timeMs != null && <span>{elapsedText(result.timeMs)}</span>}
                {result.memoryKb != null && <span>{(result.memoryKb / 1024).toFixed(1)} MB</span>}
                {result.total > 0 && <span>{result.passed || 0}/{result.total} 用例</span>}
              </div>
              {result.message && <p className="wb-result-message">{result.message}</p>}
              {result.mode === 'submit' && result.verdict === 'SAMPLE_PASS' && <p className="wb-sample-note">仅通过公开样例，暂不计入已 AC。</p>}
              {pollError && <p className="wb-poll-error" role="status">{pollError} · 正在重试</p>}
              {result.caseResults?.length > 0 && <CaseResults cases={result.caseResults} />}
              {((!result.caseResults?.length && result.output) || result.stderr) && <>
                <div className="wb-output-tabs">
                  <button type="button" aria-pressed={outputTab === 'output'} onClick={() => { setOutputTab('output'); setCopied(false); }}>标准输出</button>
                  <button type="button" aria-pressed={outputTab === 'stderr'} onClick={() => { setOutputTab('stderr'); setCopied(false); }}>诊断信息{result.stderr && <span className="wb-pending-dot" />}</button>
                  <button type="button" className="wb-copy" onClick={copyOutput} aria-label={copied ? '已复制' : '复制输出'} title={copied ? '已复制' : '复制输出'}>{copied ? <Check size={12} /> : <Copy size={12} />}</button>
                </div>
                <pre className="wb-output" tabIndex={0}>{result[outputTab] || '（无输出）'}</pre>
              </>}
            </> : <div className="wb-empty"><Terminal size={21} /><span>Ctrl+R 运行输入 · Ctrl+Enter 提交</span></div>}
          </div>}
        </div>}
      </div>
    </div>
  </section>;
}
