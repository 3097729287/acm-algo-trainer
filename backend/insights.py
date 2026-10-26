"""Pure, bounded analytics from actual submission and exact public problem evidence."""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
import datetime as dt
import hashlib
import re
import statistics
from urllib.parse import urlsplit, unquote
from progression import SHANGHAI, qualified_contests
from rating_evidence import evidence as rating_evidence
from knowledge_mastery import MODEL as KNOWLEDGE_MODEL, problem_evidence, summarize as summarize_mastery

FAILURES = {"WA", "TLE", "MLE", "RE", "CE", "OLE", "ERROR"}


def canonical_url(value):
    """Only identity-preserving first-party URL normalization; no title guessing."""
    if not isinstance(value, str) or not value:
        return None
    return _canonical_url(value.strip())


@lru_cache(maxsize=16384)
def _canonical_url(value):
    # A bounded pure identity cache avoids reparsing the same public URL in
    # every goal, receipt, achievement and alias lookup. No account data lives here.
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    host = parsed.hostname or ""
    host = host.lower().removeprefix("www.")
    path = unquote(parsed.path).rstrip("/")
    if host in {"codeforces.com", "m1.codeforces.com", "m2.codeforces.com"}:
        match = re.fullmatch(r"/(?:contest/(\d+)/problem|problemset/problem/(\d+))/([A-Za-z0-9]+)", path)
        if match:
            return f"codeforces.com/contest/{match[1] or match[2]}/problem/{match[3].upper()}"
    if host == "atcoder.jp":
        match = re.fullmatch(r"/contests/([\w-]+)/tasks/([\w-]+)", path)
        if match:
            return "atcoder.jp" + path.lower()
    if host == "luogu.com.cn":
        match = re.fullmatch(r"/problem/([A-Za-z]+\d+)", path)
        if match:
            return "luogu.com.cn/problem/" + match[1].upper()
    if host == "ac.nowcoder.com":
        match = re.fullmatch(r"/acm/contest/(\d+)/([A-Za-z0-9]+)", path)
        if match:
            return f"ac.nowcoder.com/acm/contest/{match[1]}/{match[2].upper()}"
    # Unknown domains can dedupe their own exact paths, but do not match platform facts.
    return host + path if parsed.scheme in {"http", "https"} and host else None


def _date(value):
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(SHANGHAI).date()
    except (ValueError, TypeError, AttributeError):
        try:
            return dt.date.fromisoformat(value[:10])
        except (ValueError, TypeError):
            return None


def build_insights(rows, submissions, history, workspace, hub, now):
    library = {row["id"]: row for row in rows}
    by_url = {}
    aliases = {}
    for row in rows:
        key = canonical_url(row.get("url"))
        if key:
            existing = by_url.get(key)
            if existing is None or existing.get("source") == "remote" and row.get("source") != "remote":
                by_url[key] = row
    for row in rows:
        key = canonical_url(row.get("url"))
        aliases[row["id"]] = by_url[key]["id"] if key else row["id"]
        for alias in row.get('aliasIds', []):
            aliases[alias] = aliases[row['id']]
    records = [record for record in submissions if record.get("mode") == "submit" and record.get("finished_at")]
    personal = set()      # 2026-10-10 起不再使用：本地通过不算 AC，见下方说明
    samples = set()
    independent = {}
    first_accepted = {}
    per_day = defaultdict(lambda: {"submissions": 0, "accepted": set(), "officialAccepted": set()})
    grouped = defaultdict(list)
    # 2026-10-10 口径：只有官方 AC 加经验（四档），取消本地首通 100 / 复习 20 / 模赛 10。
    from progression import official_first_xp
    xp = 0
    credited_codes = set()
    viewed_codes = set()
    reviews = defaultdict(int)
    review_cursor = {}
    for record in records:
        identity = aliases.get(record["problem_id"], record["problem_id"])
        grouped[identity].append(record)
        day = _date(record.get("submitted_at"))
        if day:
            per_day[day]["submissions"] += 1
        if record.get("verdict") == "SAMPLE_PASS":
            samples.add(identity)
        # 旧 local AC 归入样例通过展示口径（不是 AC）
        if record.get("verdict") == "AC" and record.get("scope") == "local":
            samples.add(identity)
            code_key = (identity, hashlib.sha256(record.get("code", "").encode()).hexdigest())
            if record.get("solution_seen"):
                viewed_codes.add(code_key)
            credited_codes.add(code_key)
        if record.get("verdict") != "AC" or record.get("scope") != "official":
            continue
        code_key = (identity, hashlib.sha256(record.get("code", "").encode()).hexdigest())
        if record.get("solution_seen"):
            viewed_codes.add(code_key)
        timestamp = dt.datetime.fromisoformat(record["submitted_at"].replace("Z", "+00:00"))
        if identity not in first_accepted:
            first_accepted[identity] = record.get("submitted_at")
            review_cursor[identity] = timestamp
            if day:
                per_day[day]["accepted"].add(identity)
            difficulty = library.get(identity, {}).get("difficulty")
            xp += official_first_xp(difficulty)
        credited_codes.add(code_key)
        difficulty = library.get(identity, {}).get("difficulty")
        if not record.get("solution_seen") and code_key not in viewed_codes and isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
            evidence = rating_evidence(library.get(identity, {}))
            if evidence["known"]:
                independent.setdefault(identity, (evidence["lower"], record.get("submitted_at")))

    official = set()
    for record in records:
        if record.get('mode')=='submit' and record.get('verdict')=='AC' and record.get('scope')=='official' and record.get('finished_at'):
            identity=aliases.get(record['problem_id'],record['problem_id']);official.add(identity)
    # Total solved includes verified public ACs outside the current library;
    # the knowledge/ability model below still uses known problem metadata.
    total_solved = {canonical_url(library.get(i, {}).get('url')) or 'local-id:'+i for i in official}
    solved_dates = defaultdict(set)
    for record in records:
        if record.get('verdict') == 'AC' and record.get('scope') == 'official':
            identity = aliases.get(record['problem_id'], record['problem_id'])
            key = canonical_url(library.get(identity, {}).get('url')) or 'local-id:' + identity
            day = _date(record.get('submitted_at'))
            if day:
                solved_dates[key].add(day)
    platforms = []
    for account in hub.get("accounts", []):
        platforms.append({key: account.get(key) for key in ("platform", "rating", "maxRating", "status")})
        for solved in account.get("solved", []):
            if canonical_url(solved.get('url')):
                key = canonical_url(solved['url'])
                total_solved.add(key)
                accepted_day = _date(solved.get('acceptedAt'))
                if accepted_day:
                    solved_dates[key].add(accepted_day)
            row = by_url.get(canonical_url(solved.get("url")))
            if not row:
                continue
            identity = row["id"]
            official.add(identity)
    # Attribute each canonical problem to its earliest verified AC across all
    # receipts and public account evidence, before filtering the visible dates.
    # Repeated attempts still count as activity/submissions, never as new solves.
    first_solved_days = {key: min(dates) for key, dates in solved_dates.items() if dates}
    for key, day in first_solved_days.items():
        per_day[day]["officialAccepted"].add(key)

    active = {aliases.get(row["id"], row["id"]): row for row in workspace.get("training", [])}
    reviewed = {aliases.get(row["id"], row["id"]) for row in history if row.get("review_count", 0)}
    completed_contests = qualified_contests(workspace.get("contests", []), records)
    # 2026-10-10：取消模赛本地 AC +10 XP；完成模拟赛只保留成就，不发经验。
    from tb_rank import growth as build_growth
    growth = build_growth(xp)
    today = now.astimezone(SHANGHAI).date()
    days = {day for day, value in per_day.items() if value["submissions"]}
    day = today if today in days else today - dt.timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= dt.timedelta(days=1)
    longest = current = 0
    previous = None
    for day in sorted(days):
        current = current + 1 if previous and day == previous + dt.timedelta(days=1) else 1
        longest = max(longest, current)
        previous = day
    activity = [{"date": day.isoformat(), "submissions": value["submissions"], "accepted": len(value["accepted"]), "officialAccepted": len(value["officialAccepted"])} for day, value in sorted(per_day.items()) if day <= today]

    tag_ids = defaultdict(set)
    for identity, row in library.items():
        canonical = aliases.get(identity, identity)
        names=set(row.get('tags',[]))
        names.update(part.strip() for path in row.get('knowledgeCategories',[]) for part in path.split(' / ') if part.strip())
        for tag in names:
            tag_ids[tag].add(canonical)
    mastery_evidence = problem_evidence(library, grouped, official)
    knowledge = []
    for name, ids in tag_ids.items():
        participated = ids & active.keys()
        local = ids & personal          # 旧本地 AC，仅展示；不再并入通过口径
        public = ids & official
        accepted = public               # 2026-10-10：通过 = 官方 AC
        attempts = sum(len(grouped[identity]) for identity in ids)
        failures = sum(record.get("verdict") in FAILURES for identity in ids for record in grouped[identity])
        due_ids = [identity for identity in participated if active[identity].get("queue")]
        evidence_ids = sorted(ids & mastery_evidence.keys())
        estimate = summarize_mastery(mastery_evidence[identity] for identity in evidence_ids)
        priority = min(100, len(due_ids) * 20 + (20 if participated and not accepted else 0) + min(10, failures))
        suggestions = sorted(due_ids) + sorted(ids - official - set(due_ids), key=lambda identity: (library.get(identity, {}).get("difficulty") is None, library.get(identity, {}).get("difficulty") or 99999, identity))
        reason = f"有 {len(due_ids)} 道待办" if due_ids else "已有尝试，可继续独立验证" if participated and not accepted else "继续扩大通过覆盖" if accepted else "还没有个人提交证据"
        knowledge.append({"name": name, "tags": [name], "available": len(ids), "participated": len(evidence_ids), "accepted": len(accepted), "officialAccepted": len(public), "localAccepted": len(local), "attempts": attempts, "failures": failures, "due": len(due_ids), "dueIds": sorted(due_ids), "reviewed": len(ids & reviewed), **estimate, "evidenceIds": evidence_ids, "label": "个人作答掌握度" if estimate['mastery'] is not None else "证据不足", "priority": priority, "reason": reason, "suggestedIds": suggestions[:6]})
    knowledge.sort(key=lambda item: (-item["priority"], item["name"]))
    recommendations = [{"name": item["name"], "reason": item["reason"], "priority": item["priority"], "ids": item["suggestedIds"]} for item in knowledge if item["suggestedIds"]][:6]

    from progression import ac_achievements, official_reward_evidence
    achievements = ac_achievements(official_reward_evidence(rows, records, hub))
    achievements.append({"id": "contest-1", "name": "完成模拟赛", "description": "完成一场至少训练一分钟并实际提交的计时模拟赛", "unlocked": bool(completed_contests), "unlockedAt": min((item.get("finishedAt") for item in completed_contests if item.get("finishedAt")), default=None), "progress": min(1, len(completed_contests)), "target": 1})
    evidence_count = len(independent)
    enough = evidence_count >= 5
    rating = int(round(statistics.median(value[0] for value in independent.values()) / 100) * 100) if enough else None
    trend = []
    seen_values = []
    for difficulty, timestamp in sorted(independent.values(), key=lambda value: value[1] or ""):
        seen_values.append(difficulty)
        day = _date(timestamp)
        if len(seen_values) >= 5 and day:
            point = {"date": day.isoformat(), "value": int(round(statistics.median(seen_values) / 100) * 100)}
            if trend and trend[-1]["date"] == point["date"]:
                trend[-1] = point
            else:
                trend.append(point)
    assessment = {"rating": rating, "band": "insufficient" if not enough else "low" if evidence_count < 10 else "medium" if evidence_count < 30 else "high", "label": "训练难度估算" if enough else "独立通过证据不足", "confidence": "none" if not enough else "low" if evidence_count < 10 else "medium" if evidence_count < 30 else "high", "evidenceCount": evidence_count, "explanation": "取至少五道独立官方 AC 题目的难度中位数，非 CF 官方难度采用保守区间下界，仅描述已验证训练范围，不是官方等级分；查看题解后的提交、运行和样例通过不计入。", "platforms": platforms, "trend": trend[-365:]}
    recommendations, level, basis = recommend_problems(library, active, independent, personal, official, hub)
    assessment.update(recommendationLevel=level, recommendationBasis=basis)
    before_today_solved = {key for key in total_solved if not solved_dates[key] or any(day < today for day in solved_dates[key])}
    today_solved = {key for key in total_solved if first_solved_days.get(key) == today}
    summary = {"beforeTodaySolved": len(before_today_solved), "todaySolved": len(today_solved), "active": len(active), "accepted": sum(bool(row.get("accepted")) for row in active.values()), "submissions": len(records), "activeDays": len(days), "streak": streak, "longestStreak": longest, "completedContests": len(completed_contests), "officialSolved": len(official), "totalSolved": len(total_solved), "localAccepted": len(personal), "samplePassed": len(samples)}
    ac_days=sorted(day for day,value in per_day.items() if value['officialAccepted'] and day<=today)
    longest_ac=current_ac=0;previous_ac=None
    for day in ac_days:
        current_ac=current_ac+1 if previous_ac and day==previous_ac+dt.timedelta(days=1) else 1
        longest_ac=max(longest_ac,current_ac);previous_ac=day
    best_day=max(ac_days,key=lambda day:len(per_day[day]['officialAccepted']),default=None)
    hardest=max((library[identity] for identity in official if identity in library and type(library[identity].get('difficulty')) in (int,float)),
                key=lambda row:(row['difficulty'],row['id']),default=None)
    personal_statistics={'longestAcStreak':longest_ac,'maxDailyAc':len(per_day[best_day]['officialAccepted']) if best_day else 0,
                         'maxDailyAcDate':best_day.isoformat() if best_day else None,
                         'hardestSolved':{key:hardest.get(key) for key in ('id','title','contest','problem','difficulty')} if hardest else None}
    return {"summary": summary, "personalStatistics":personal_statistics, "growth": growth, "activity": activity, "knowledge": knowledge, "knowledgeEvidence": list(mastery_evidence.values()), "knowledgeModel": dict(KNOWLEDGE_MODEL), "recommendations": recommendations, "achievements": achievements, "assessment": assessment}


def recommend_problems(library, active, independent, personal, official, hub):
    """Practice targets are conservative training bands, never fabricated ratings."""
    values = [value[0] for value in independent.values()]
    cf = [account.get('rating') for account in hub.get('accounts', []) if account.get('platform') == 'codeforces' and account.get('status') == 'ready' and isinstance(account.get('rating'), (int, float)) and not isinstance(account.get('rating'), bool)]
    public = [library[identity]['difficulty'] for identity in official if identity in library and isinstance(library[identity].get('difficulty'), (int, float))]
    if len(values) >= 3:
        level = round(statistics.median(values) / 100) * 100
        basis = f'根据 {len(values)} 道独立官方 AC 题的难度选择邻近训练带；这不是官方等级分'
    elif cf:
        level = round((cf[0] - 100) / 100) * 100
        basis = '使用已绑定 Codeforces 官方等级分保守选择训练带；其它平台分数不混算'
    elif len(public) >= 5:
        level = round(statistics.median(public) / 100) * 100
        basis = '根据原站通过与题库精确匹配的题目难度选择训练带，独立完成情况未知'
    else:
        level = 1100
        basis = '独立证据不足，先从 1000–1250 的基础题起步；这是起步建议，不是能力测量'
    level = int(min(2100, max(1000, level)))
    lower, upper = max(1000, level - 150), min(2199, level + (150 if len(values) >= 5 else 100))
    if not values and not cf and len(public) < 5:
        lower, upper = 1000, 1250
    known = official  # 2026-10-10：已解 = 官方 AC；本地样例通过不算已解
    foundation = {'模拟', '枚举', '排序', '前缀和', '差分', '贪心', '双指针', '二分查找', '数组', '字符串'}
    graph = {'图论', 'BFS', 'DFS', '并查集', '树', '最短路'}
    basics = {identity for identity in known if foundation & set(library.get(identity, {}).get('tags', []))}
    graphs = {identity for identity in known if graph & set(library.get(identity, {}).get('tags', []))}
    def tier(row):
        text = ' '.join(row.get('tags', []))
        if any(word in text for word in ('Hall', '霍尔', '网络流', '最大流', '最小割', '二分图匹配', 'DFS序', 'DFS 序', '树链剖分', '后缀自动机', '线段树', '树状数组', '数位 DP', '状压 DP')):
            return 3
        if any(word in text for word in ('DP', '动态规划', '图论', 'BFS', 'DFS', '最短路', '并查集', '树')):
            return 2
        return 1
    ranked = []
    for identity, row in library.items():
        if row.get('catalogHidden') and not active.get(identity, {}).get('queue'):
            continue
        difficulty = row.get('difficulty')
        if not isinstance(difficulty, (int, float)) or isinstance(difficulty, bool) or not lower <= difficulty <= upper:
            continue
        due = active.get(identity, {}).get('queue')
        if identity in known and not due:
            continue
        order = tier(row)
        if order == 2 and len(basics) < 2 or order == 3 and (len(basics) < 5 or len(graphs) < 2 or level < 1700):
            continue
        score = (0 if due else 1, abs(difficulty - level), order, 0 if row.get('source') != 'remote' else 1, identity)
        ranked.append((score, row, due, order))
    ranked.sort(key=lambda item: item[0])
    result, seen_urls, seen_ids, main_tags = [], set(), set(), set()
    for _, row, due, order in ranked:
        identity = row['id']; key = canonical_url(row.get('url'))
        if identity in seen_ids or key and key in seen_urls:
            continue
        tag = (row.get('tags') or ['基础练习'])[0]
        # After the first pass, allow repeated topics when no varied candidate exists.
        if tag in main_tags and len(result) >= 3:
            continue
        seen_ids.add(identity); main_tags.add(tag)
        if key:seen_urls.add(key)
        stage = 'retry' if due else 'foundation' if order == 1 and len(basics) < 2 else 'stretch' if row['difficulty'] > level else 'consolidate'
        reason = f'优先完成当前待办，难度 {row["difficulty"]} 在适合的训练带内' if due else f'难度 {row["difficulty"]} 接近当前建议 {level}；先练基础技巧' if stage == 'foundation' else f'已有基础证据，选择邻近难度 {row["difficulty"]}，逐步提高' if stage == 'stretch' else f'难度 {row["difficulty"]} 接近当前训练带，可巩固 {tag}'
        result.append({'name':tag,'reason':reason,'priority':100-len(result)*5,'ids':[identity],
          'problem':{name:row.get(name) for name in ('id','title','difficulty','platform','contest','tags')},
          'stage':stage,'band':{'min':lower,'max':upper,'target':level}})
        if len(result) >= 6:break
    return result, level, basis
