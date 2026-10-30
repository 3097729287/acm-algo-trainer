import MedalEmblem, {titleMedalIndex} from './MedalEmblem.jsx';
import Tooltip from './Tooltip.jsx';
export default function TitleMedals({titles=[],compact=false,iconOnly=false}){
  if(!titles?.length)return null;
  return <span className={`title-medals${compact?' title-medals-compact':''}`} aria-label="已获得称号">{titles.map(item=>{
    const targets=item.category==='streak'?[30,90,180,365,730]:[500,750,1000,1500,2000],index=targets.indexOf(Number(item.target));
    return <Tooltip key={item.id} text={`${item.name} · ${item.category==='streak'?'连续训练':'AC'} ${Number(item.target).toLocaleString('zh-CN')} ${item.category==='streak'?'天':'题'}`}><span className={`title-medal title-medal-${item.category||'ac'}`} tabIndex={0} aria-label={item.name}><MedalEmblem index={titleMedalIndex(item)} variant={item.category==='streak'?'streak':'ac'} size={compact?22:26}/>{!iconOnly&&<span>{item.name}</span>}</span></Tooltip>;
  })}</span>;
}
