import {activateStudyTab,studyGroups} from './learningBrowser.js';

export const SECTION_DIVIDER_WIDTH=5;

// Fit preferred proportions to the space that remains after the dividers.
// A pane at its content minimum stays fixed while the others share the rest.
export function sectionSplitLayout(groups,width,minimums,divider=SECTION_DIVIDER_WIDTH){
 const available=Math.max(0,width-divider*Math.max(0,groups.length-1));
 const minima=groups.map((_,index)=>Math.max(0,minimums[index]||0));
 if(groups.length<2)return {stacked:false,available,widths:groups.map(()=>available),minimums:minima.map(value=>Math.min(value,available))};
 const stacked=groups.length>1&&minima.reduce((sum,value)=>sum+value,0)>available+.01;
 if(stacked)return {stacked,available,widths:groups.map(()=>width),minimums:minima};
 const widths=groups.map(()=>0),pending=new Set(groups.map((_,index)=>index));
 let remaining=available;
 while(pending.size){
  const total=[...pending].reduce((sum,index)=>sum+groups[index].weight,0)||pending.size;
  const fixed=[...pending].filter(index=>remaining*(groups[index].weight||1)/total<minima[index]);
  if(!fixed.length){for(const index of pending)widths[index]=remaining*(groups[index].weight||1)/total;break;}
  for(const index of fixed){widths[index]=minima[index];remaining-=widths[index];pending.delete(index);}
 }
 return {stacked,available,widths,minimums:minima};
}

export function resizeSectionSplit(state,index,position,width,minimums,{center=false,snap=12}={}){
 const groups=studyGroups(state),layout=sectionSplitLayout(groups,width,minimums);
 if(layout.stacked||!groups[index+1]||!layout.available)return state;
 const before=layout.widths.slice(0,index).reduce((sum,value)=>sum+value,0)+index*SECTION_DIVIDER_WIDTH;
 const total=layout.widths[index]+layout.widths[index+1],low=minimums[index],high=total-minimums[index+1];
 const midpoint=total/2;
 let left=center?midpoint:position-before-SECTION_DIVIDER_WIDTH/2;
 if(midpoint>=low&&midpoint<=high&&Math.abs(left-midpoint)<=snap)left=midpoint;
 left=Math.max(low,Math.min(high,left));
 const widths=[...layout.widths];widths[index]=left;widths[index+1]=total-left;
 const next=groups.map((group,at)=>({...group,weight:widths[at]/layout.available*100}));
 if(next.every((group,at)=>Math.abs(group.weight-groups[at].weight)<.0001))return state;
 return activateStudyTab({...state,groups:next},state.focused);
}
