import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import LearningPathsPage from '../src/pages/LearningPathsPage.jsx';
import { SEQUENCE_PROBLEMS } from '../src/pages/algorithm-lab/sequenceProblems.js';
import '../standalone/labShell.css';

function Fixture() {
  const [prefs, setPrefs] = useState({ learningPaths: {} }), [locked, setLocked] = useState([]);
  const rows = Object.values(SEQUENCE_PROBLEMS).flat().map(p => ({ id: `existing:${p.pid}`, url: p.url.replace('/problemset/problem/', '/contest/').replace(/\/([A-Z])$/, '/problem/$1') }));
  useEffect(() => { window.sequenceFixture = { prefs, lock: setLocked, seed: setPrefs, rows }; }, [prefs]);
  return <LearningPathsPage standalone prefs={prefs} setPrefs={setPrefs} rows={rows} lockedProblems={locked} onTrain={(id, options) => { window.sequenceTraining = { id, options }; }}/ >;
}
createRoot(document.getElementById('root')).render(<Fixture/>);
