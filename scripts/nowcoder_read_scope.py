"""Read full original statements in small batches without printing whole registries."""
import argparse
import json
from nowcoder_editorials import CONTENT, database, read


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('list_number')
    parser.add_argument('start', type=int, nargs='?', default=0)
    parser.add_argument('count', type=int, nargs='?', default=6)
    parser.add_argument('--titles', action='store_true')
    args = parser.parse_args()
    known = set(read(CONTENT / 'reviewed.json')) | {
        k for k, v in read(CONTENT / 'ratings.json').items() if v['difficulty'] > 2300}
    connection = database()
    list_id = args.list_number if args.list_number.startswith('nowcoder-') else 'nowcoder-contest-' + args.list_number
    listing = json.loads(connection.execute('SELECT content FROM training_lists WHERE id=?',
                                           (list_id,)).fetchone()[0])
    rows = [q['problemId'] for q in listing['problems'] if q['problemId'] not in known]
    print('Unreviewed:', len(rows))
    for identity in (rows if args.titles else rows[args.start:args.start + args.count]):
        problem = json.loads(connection.execute('SELECT encoded FROM problems WHERE id=?', (identity,)).fetchone()[0])
        print(identity, problem['title'])
        if args.titles:
            continue
        statement = json.loads(connection.execute('SELECT content FROM statements WHERE problem_id=?', (identity,)).fetchone()[0])
        print(statement['markdown'])
        print('SAMPLES:', json.dumps(statement.get('samples'), ensure_ascii=False))
    connection.close()


if __name__ == '__main__':
    main()
