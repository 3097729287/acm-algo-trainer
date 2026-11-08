"""Prefer the verified original Nowcoder difficulty over any counterpart estimate."""
from nowcoder_editorials import CONTENT, database, read, sha, write
import json


def main():
    official = read(CONTENT / 'official-ratings.json')
    ledger = read(CONTENT / 'reviewed.json')
    ratings = read(CONTENT / 'ratings.json')
    db = database()
    for identity, original in official['scope'].items():
        number = original['difficulty']
        if number is None:
            continue
        problem = json.loads(db.execute('SELECT encoded FROM problems WHERE id=?', (identity,)).fetchone()[0])
        statement = json.loads(db.execute('SELECT content FROM statements WHERE problem_id=?', (identity,)).fetchone()[0])
        source = {'platform': 'Nowcoder', 'url': original['sourceUrl'], 'rating': number,
                  'ratingVerifiedAt': official['checkedAt'], 'sourceHtmlSha256': original['sourceHtmlSha256'],
                  'column': 'difficulty', 'acceptedUsersSeparateColumn': original['acceptedUsers'],
                  'originalListTitle': original['title']}
        for table in ([ratings, ledger] if identity in ledger else [ratings]):
            entry = table.setdefault(identity, {'id': identity, 'url': problem['url'], 'title': problem['title'],
                                               'knowledge': [], 'statementSha256': sha(statement['markdown'])})
            if not entry.get('ratingOrigin') and 'difficulty' in entry:
                entry['priorDifficultyReview'] = {k: entry.get(k) for k in ['difficulty', 'difficultyEstimated', 'difficultyReason', 'origin']}
            entry.update(difficulty=number, difficultyEstimated=False, ratingOrigin=source,
                         difficultyReason=f'已核对牛客公开题库列表中的NC{identity.split("::")[-1]}行：难度列为{number}；相邻通过人数列为{original["acceptedUsers"]}，两者分别解析。原始页面SHA256与查询URL已保存。以此原站评级替代此前估分。')
    db.close()
    write(CONTENT / 'ratings.json', ratings)
    write(CONTENT / 'reviewed.json', ledger)
    print('Verified original-platform ratings:', official['ratedScope'], 'of', official['scopeTotal'])


if __name__ == '__main__':
    main()
