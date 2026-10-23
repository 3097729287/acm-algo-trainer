import KnapsackLab from './KnapsackLab.jsx';
import GuidedWorkshop from './GuidedWorkshop.jsx';

export default function KnapsackCourse(props) {
  const guided = props.prefs.learningPaths?.knapsack?.mode === 'guided';
  const changeMode = () => props.setPrefs(previous => ({ ...previous, learningPaths: { ...previous.learningPaths, knapsack: { ...previous.learningPaths?.knapsack, mode: guided ? 'learn' : 'guided' } } }));
  const actions = <>{props.headerActions}<button type="button" className="lab-icon-button lab-mode-switch" aria-label="返回学算法" title="学算法" onClick={changeMode}>课程</button></>;
  return guided ? <GuidedWorkshop {...props} headerActions={actions}/> : <KnapsackLab {...props} onGuided={changeMode} headerActions={props.headerActions}/>;
}
