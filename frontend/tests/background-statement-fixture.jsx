import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { EditorView } from '@codemirror/view';
import Workbench from '../src/app/Workbench.jsx';
import 'katex/dist/katex.min.css';

const style = document.createElement('style');
style.textContent = `:root{font-family:"Segoe UI","Microsoft YaHei UI",sans-serif;--bg:#f5f6f8;--panel:#fff;--panel-2:#f7f8fa;--text:#262b38;--muted:#657087;--line:#dfe4eb;--accent:#137e6c;--accent-soft:#137e6c14;--success:#137e6c;--danger:#be394c;--warning:#a16419}*{box-sizing:border-box}body{margin:0;padding:18px;background:var(--bg)}#root{height:calc(100dvh - 36px);min-height:500px}.fixture{height:100%}`;
document.head.append(style);

const plans = Object.fromEntries(['A', 'B', 'C', 'F', 'E', 'CLOUD', 'EMPTY'].map(id => [id, { mode: ['C', 'CLOUD', 'EMPTY'].includes(id) ? 'ready' : 'loading' }]));
const drafts = Object.fromEntries(Object.keys(plans).map(id => [`solo:${id}`, `// saved draft ${id}\n`]));
const pending = [];
const fixture = window.backgroundStatementFixture = {
  calls: [], answers: [], drafts,
  pending: () => pending.filter(item => !item.done).map(({ id, callId }) => ({ id, callId })),
  arm: id => { plans[id].mode = 'hold'; },
  ready: id => { plans[id].mode = 'ready'; },
  cloudDraft(id, code, savedAt) {
    fixture.drafts[`solo:${id}`] = code;
    plans[id].draftSavedAt = savedAt;
  },
  localDraft(id, code, modifiedAt) {
    const key = `tb.draft.v2.solo.${encodeURIComponent(id)}`;
    localStorage.setItem(key, JSON.stringify({ code, dirty: true, owner: 'old-device-fixture', version: 3, modifiedAt }));
    return key;
  },
  readCode: () => EditorView.findFromDOM(document.querySelector('.cm-content')).state.doc.toString(),
  release(id, overrides = {}, error = '') {
    let count = 0;
    for (const item of pending.filter(row => row.id === id && !row.done)) {
      item.done = true;
      fixture.answers.push({ id, callId: item.callId, error, at: Date.now() });
      if (error) item.reject(new Error(error));
      else item.resolve({ ...problem(id, true), ...overrides });
      count++;
    }
    return count;
  },
};

function problem(id, ready = false) {
  return {
    id, title: `Fixture ${id} 题目`, url: `${location.origin}/fixture-original/${id}`,
    markdown: ready ? `# Statement ${id}\n\nOnly statement ${id}: compute $a+b$.\n\n## Input\n\nTwo integers.\n\n## Output\n\nTheir sum.` : '',
    statementAvailable: ready, statementLoading: !ready, statementError: '',
    samples: ready ? [{ name: '样例 1', input: '1 2\n', output: '3\n' }] : [],
    limits: { timeMs: 2000, memoryMb: 256 }, judge: { scope: 'samples', label: '样例评测', cases: 1 },
    locked: false, draft: fixture.drafts[`solo:${id}`] || '', draftSavedAt: plans[id].draftSavedAt || null, submissions: [],
  };
}

async function api(path, body) {
  const call = { callId: fixture.calls.length + 1, path, body, at: Date.now() };
  fixture.calls.push(call);
  const url = new URL(path, `${location.origin}/`);
  if (url.pathname === '/problem') {
    const id = url.searchParams.get('id');
    call.id = id;
    call.background = url.searchParams.get('background');
    call.refresh = url.searchParams.get('refresh');
    if (!plans[id]) throw new Error(`Unknown fixture problem ${id}`);
    if (plans[id].mode === 'hold') {
      return new Promise((resolve, reject) => pending.push({ id, callId: call.callId, done: false, resolve, reject }));
    }
    return problem(id, plans[id].mode === 'ready');
  }
  if (path === 'draft') {
    fixture.drafts[`${body.contestId || 'solo'}:${body.id}`] = body.code;
    return { savedAt: new Date().toISOString() };
  }
  // The fixture has no browser, provider, submission, or remote-site service.
  throw new Error(`Unexpected fixture API call ${path}`);
}

function Fixture() {
  const [id, setId] = useState('A');
  fixture.changeProblem = setId;
  return <div className="fixture"><Workbench problemId={id} contest={null} api={api} /></div>;
}
createRoot(document.getElementById('root')).render(<React.StrictMode><Fixture /></React.StrictMode>);
