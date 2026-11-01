import MedalEmblem, {titleMedalIndex} from './MedalEmblem.jsx';
import Tooltip from './Tooltip.jsx';
export default function TitleMedals({titles=[],compact=false,iconOnly=false,medalSize}){
  if(!titles?.length)return null;
  return <span className={`title-medals${compact?' title-medals-compact':''}`} aria-label="已获得称号">{titles.map(item=>{
    const requirement=item.category==='difficulty'?`难度 ${item.target}`:`${item.category==='streak'?'连续训练':'AC'} ${Number(item.target).toLocaleString('zh-CN')} ${item.category==='streak'?'天':'题'}`;
    return <Tooltip key={item.id} text={`${item.name} · ${requirement}`}><span className={`title-medal title-medal-${item.category||'ac'}`} tabIndex={0} aria-label={item.name}><MedalEmblem index={titleMedalIndex(item)} variant={item.category||'ac'} size={medalSize??(compact?22:26)}/>{!iconOnly&&<span>{item.name}</span>}</span></Tooltip>;
  })}</span>;
}
