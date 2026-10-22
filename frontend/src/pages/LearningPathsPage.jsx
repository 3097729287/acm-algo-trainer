import { ArrowLeft, BookOpen, Code2 } from 'lucide-react';
import KnapsackCourse from './algorithm-lab/KnapsackCourse.jsx';
import './algorithm-lab/algorithmLab.css';

export default function LearningPathsPage({ rows = [], prefs, setPrefs, onTrain, lockedProblems = [] }) {
  const open = mode => setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: 'knapsack', knapsack: { ...previous.learningPaths?.knapsack, mode } } }));
  const back = () => setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, activePath: null } }));
  return <div className="learning-paths-page scroll-panel" aria-label="算法实验室">
    {prefs.learningPaths?.activePath === 'knapsack' ? <KnapsackCourse rows={rows} prefs={prefs} setPrefs={setPrefs} onTrain={onTrain} lockedProblems={lockedProblems} headerActions={<button type="button" className="lab-icon-button" aria-label="返回算法实验室" title="返回算法实验室" onClick={back}><ArrowLeft size={17}/></button>}/> : <div className="lab-catalog lab-only-course">
      <h2>算法实验室</h2><section className="lab-panel"><h3>背包 DP</h3><p>先学会推导，再跟着做 5 道题。</p><div className="lab-course-options"><button type="button" className="lab-button" onClick={() => open('learn')}><BookOpen size={17}/>学算法</button><button type="button" className="lab-button lab-button-quiet" onClick={() => open('guided')}><Code2 size={17}/>跟着做题</button></div></section>
    </div>}
  </div>;
}
