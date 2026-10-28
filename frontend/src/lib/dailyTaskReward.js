// Apply only XP already committed and acknowledged by the claim endpoint.
export function applyDailyTaskReward(insights,result) {
 const value={...insights,dailyTasks:result.dailyTasks},previous=insights?.growth,award=Number(result.awardedXp)||0;
 if(!previous||award<=0||!Array.isArray(previous.levelCosts))return value;
 const costs=previous.levelCosts,xp=Number(previous.xp??previous.totalXp)+award;
 let level=1,remaining=xp;
 for(const cost of costs){if(remaining<cost)break;remaining-=cost;level++;}
 const capped=level>=previous.levelCap,cost=capped?0:costs[level-1];
 value.growth={...previous,xp,totalXp:xp,missionXp:(previous.missionXp||0)+award,level,levelName:`Lv.${level}`,currentLevelXp:capped?0:remaining,nextLevelXp:cost,rankedEligible:previous.rankedEligible||level>=previous.rankUnlockLevel,nextMilestone:capped?'已达等级上限':`再积累 ${cost-remaining} XP 升至 ${level+1} 级`};
 return value;
}
