import { memo, lazy, Suspense } from 'react';
import './InlineTitle.css';
const MathTitle = lazy(() => import('./MathTitle.jsx'));

export default memo(function InlineTitle({ children }) {
  const text = String(children ?? '');
  // Ordinary names keep their literal punctuation and avoid Markdown parsing.
  if (!/\$|\\\(|\\\[/.test(text)) return text;
  return <Suspense fallback={text}><MathTitle text={text} /></Suspense>;
});
