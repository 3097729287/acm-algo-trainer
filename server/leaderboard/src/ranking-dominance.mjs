import {addDays,bounds} from './ranking-rules.mjs';
import {firstOfficialEventsCTE,questionNotExcludedSQL} from './question-identities.mjs';

export function dominanceFromDays(days,today) {
  const unique=[...new Set(days)].filter(day=>/^\d{4}-\d{2}-\d{2}$/.test(day)&&day<today).sort();
  let longest=0,current=0,previous=null;
  for(const day of unique){current=previous&&addDays(previous,1)===day?current+1:1;longest=Math.max(longest,current);previous=day;}
  return {days:previous===addDays(today,-1)?current:0,totalDays:unique.length,longestDays:longest};
}

export class RankingDominance {
  constructor(database,dialect='mysql'){this.database=database;this.dialect=dialect;this.checkedAt=0;this.enabled=false;}
  async available(){
    if(Date.now()-this.checkedAt<10000)return this.enabled;
    try{await this.database.execute('SELECT period,ranking_day FROM ranking_leader_days LIMIT 0');this.enabled=true;}
    catch(error){if(!['ER_NO_SUCH_TABLE','ER_BAD_FIELD_ERROR'].includes(error.code)&&!/no such (?:table|column)/i.test(error.message||''))throw error;this.enabled=false;}
    this.checkedAt=Date.now();return this.enabled;
  }
  async settle(now){
    if(!await this.available())return;
    const today=bounds('daily',now).day,timestamp=new Date(now).toISOString(),ignore=this.dialect==='mysql'?'INSERT IGNORE':'INSERT OR IGNORE';
    await this.database.transaction(async connection=>{
      const schedule=this.dialect==='mysql'?'INSERT INTO ranking_leader_schedule(singleton,next_day) VALUES(1,?) ON DUPLICATE KEY UPDATE singleton=singleton':'INSERT OR IGNORE INTO ranking_leader_schedule(singleton,next_day) VALUES(1,?)';
      // Take the exclusive singleton lock immediately. INSERT IGNORE can hold
      // shared duplicate-key locks that deadlock on concurrent FOR UPDATE.
      await connection.execute(schedule,[today]);
      // Only settled daily awards establish history from before this feature.
      // Weekly/all-time holding days begin with actual daily observations.
      await connection.execute(`${ignore} INTO ranking_leader_days(period,ranking_day,user_id,score,observed_at) SELECT 'daily',start_date,user_id,0,settled_at FROM ranking_rewards WHERE period='daily' AND position=1`);
      const [settings]=await connection.execute('SELECT next_day FROM ranking_leader_schedule WHERE singleton=1'+(this.dialect==='mysql'?' FOR UPDATE':''));
      let day=settings[0].next_day,steps=0;
      while(day<today&&steps++<366){
        const end=addDays(day,1),cutoff=new Date(end+'T00:00:00+08:00').toISOString();
        for(const period of ['daily','weekly','total']){
          const range=period==='total'?null:period==='daily'?{start:day,end}: {...bounds('weekly',Date.parse(day+'T12:00:00+08:00')),end};
          const [leaders]=await connection.execute(`WITH ${firstOfficialEventsCTE()} SELECT e.user_id,COUNT(*) AS score,MAX(e.accepted_at) AS completed_at FROM first_official_ac e JOIN accounts a ON a.user_id=e.user_id WHERE e.received_at<? AND e.accepted_day<? ${range?'AND e.accepted_day>=?':''} AND ${questionNotExcludedSQL()} GROUP BY e.user_id ORDER BY score DESC,completed_at,e.user_id LIMIT 1`,[cutoff,end,...range?[range.start]:[]]);
          const leader=leaders[0];
          if(leader&&Number(leader.score)>0)await connection.execute(`${ignore} INTO ranking_leader_days(period,ranking_day,user_id,score,observed_at) VALUES(?,?,?,?,?)`,[period,day,leader.user_id,Number(leader.score),timestamp]);
        }
        day=end;
      }
      await connection.execute('UPDATE ranking_leader_schedule SET next_day=? WHERE singleton=1',[day]);
    });
  }
  async summary(ids,period,today){
    const unique=[...new Set(ids)].slice(0,201);
    if(!unique.length||!['daily','weekly','total'].includes(period)||!await this.available())return new Map();
    const [rows]=await this.database.execute(`SELECT user_id,ranking_day FROM ranking_leader_days WHERE period=? AND user_id IN (${unique.map(()=>'?').join(',')}) ORDER BY ranking_day`,[period,...unique]);
    return new Map(unique.map(id=>[id,dominanceFromDays(rows.filter(row=>row.user_id===id).map(row=>row.ranking_day),today)]));
  }
}
