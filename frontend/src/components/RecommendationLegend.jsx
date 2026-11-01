import {RECOMMENDATION_KINDS} from '@/lib/recommendationKinds.js';

export default function RecommendationLegend(){
 return <section className="recommendation-legend" aria-label="推荐任务图标"><h3>推荐任务图标</h3><dl>{Object.entries(RECOMMENDATION_KINDS).map(([kind,{Icon,label,meaning}])=><div key={kind} data-recommendation-kind={kind}><dt><Icon size={19} aria-hidden="true"/><strong>{label}</strong></dt><dd>{meaning}</dd></div>)}</dl></section>;
}
