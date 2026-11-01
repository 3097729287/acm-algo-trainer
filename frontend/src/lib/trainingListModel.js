import {filterTrainingListsScope} from './trainingCurriculum.js';
import {platformTrainingLists} from './trainingListPlatforms.js';
import {organizeTrainingLists} from './trainingListCatalog.js';
import {trainingIndex} from './trainingLists.js';

// Weak keys release old accounts/catalogues; a few modes/favorite combinations
// can reuse the same resolved index when a list is opened or revisited.
const cache=new WeakMap();
export function trainingListModel(lists,rows,mode,favoriteIds=[]) {
 let byRows=cache.get(lists);if(!byRows){byRows=new WeakMap();cache.set(lists,byRows);}
 let variants=byRows.get(rows);if(!variants){variants=new Map();byRows.set(rows,variants);}
 const key=JSON.stringify([mode,[...favoriteIds].sort()]);
 if(variants.has(key))return variants.get(key);
 const original=filterTrainingListsScope(organizeTrainingLists(lists.filter(list=>!list.custom)),rows);
 const favorites=new Set(favoriteIds);
 const favorite={id:'personal:favorites',title:'我的收藏',displayTitle:'我的收藏',virtual:true,available:true,aggregateChildren:false,children:[],categories:[{id:'personal',name:'我的题单',order:-1}],topicPath:[],problems:rows.filter(row=>[row.id,...row.aliasIds||[]].some(id=>favorites.has(id))).map(row=>({problemId:row.id,pid:row.problem,url:row.url,sections:[]}))};
 const organized=filterTrainingListsScope([...platformTrainingLists(original,rows,mode),...lists.filter(list=>list.custom).map(list=>({...list,displayTitle:list.title,sourceLabel:'',topicPath:['我的题单']})),favorite],rows);
 const model={organized,index:trainingIndex(organized,rows)};
 if(variants.size>=8)variants.delete(variants.keys().next().value);
 variants.set(key,model);return model;
}
