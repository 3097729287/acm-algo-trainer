import React from 'react';
import { createRoot } from 'react-dom/client';
import { CompetitionPage, ActivityPage } from '../src/pages/ProgressPanels.jsx';
import '../src/styles/workspace.css';
import '../src/styles/unified.css';
document.documentElement.dataset.theme = 'dark';
const rows = [
  ['周赛 2', '牛客', '牛客周赛'], ['周赛 10', '牛客', '牛客周赛'],
  ['月赛 1', '洛谷', '洛谷月赛'], ['Div.2 1', 'Codeforces', 'Div.2'],
  ['ABC 1', 'AtCoder', 'ABC'], ['ICPC 2025 南京区域赛', 'Codeforces', 'XCPC'],
  ['蓝桥杯 2025 初赛', '洛谷', '蓝桥杯 C/C++大学B'],
].map(([contest, platform, series], index) => ({ id: 'fixture-' + index, contest, platform,
  series, title: '题目 ' + index, problem: 'A', difficulty: index === 5 ? null : 1100,
  difficultyEstimated: platform !== 'Codeforces', examYear: 2025, examStage: '区域赛' }));
const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai' }).format(new Date());
const activity = [0, 1, 2, 4, 7].map((officialAccepted, index) => ({
  date: today.slice(0, 8) + String(index + 1).padStart(2, '0'),
  officialAccepted, submissions: 50, accepted: 30,
}));
createRoot(document.getElementById('root')).render(<main style={{ padding: 20, height: '100vh', overflow: 'auto' }}>
  <CompetitionPage rows={rows} workspace={{ training: [] }} />
  <ActivityPage insights={{ activity, summary: {} }} />
</main>);
