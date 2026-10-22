import KnapsackLab from './KnapsackLab.jsx';
import GuidedWorkshop from './GuidedWorkshop.jsx';

export default function KnapsackCourse(props) {
  const guided = props.prefs.learningPaths?.knapsack?.mode === 'guided';
  const changeMode = () => props.setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, knapsack: { ...previous.learningPaths?.knapsack, mode: guided ? 'learn' : 'guided' } } }));
  const actions = <><button type="button" className="lab-icon-button lab-mode-switch" aria-label={guided ? '返回学算法' : '进入跟着做题'} title={guided ? '学算法' : '跟着做题'} onClick={changeMode}>{guided ? '课程' : '跟做'}</button>{props.headerActions}</>;
  return guided ? <GuidedWorkshop {...props} headerActions={actions}/> : <KnapsackLab {...props} headerActions={actions}/>;
}
