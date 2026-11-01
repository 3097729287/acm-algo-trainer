import {Square} from 'lucide-react';
import './LessonLearnedButton.css';

export default function LessonLearnedButton({learned=false,onClick,size=15,label}){
 const action=learned?'取消已学会':'标记已学会';
 return <button type="button" className="icon-button lesson-learned-toggle" aria-label={label||action} title={action} aria-pressed={learned} onClick={onClick}>
  <Square size={size} fill={learned?'currentColor':'none'}/>
 </button>;
}
