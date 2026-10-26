import { memo, lazy, Suspense } from 'react';
import './InlineTitle.css';
import {problemTitle} from '../lib/problemTitle.js';
const MathTitle = lazy(() => import('./MathTitle.jsx'));

export default memo(function InlineTitle({ children }) {
  const text = problemTitle(children);
  // Ordinary names keep their literal punctuation and avoid Markdown parsing.
  if (!/\$|\\\(|\\\[/.test(text)) return text;
  return <Suspense fallback={text}><MathTitle text={text} /></Suspense>;
});
