"""Independent brute oracles for periods, palindrome values and prefix versions."""
import itertools
import random
import subprocess

from nowcoder_editorials import CONTENT, OUT, read, write

RNG = random.Random(2026110807)
COUNTS = {}


def run(number, data, expected):
    result = subprocess.run([str(OUT / 'compiled' / str(number) / 'main.exe')],
                            input=data.encode(), capture_output=True, timeout=6)
    actual = result.stdout.decode()
    assert result.returncode == 0 and actual.split() == str(expected).split(), (number, data[:1000], expected, actual[:1000])
    COUNTS[str(number)] = COUNTS.get(str(number), 0) + 1


def periods_and_lexicography():
    for _ in range(35):
        n, m = RNG.randint(1, 4), RNG.randint(1, 4)
        colors = [''.join(RNG.choice('ab') for j in range(m)) for i in range(n)]
        costs = [[RNG.randint(0, 10) for j in range(m)] for i in range(n)]
        best = 10 ** 9
        for p in range(1, n + 1):
            for q in range(1, m + 1):
                if any(colors[i][j] != colors[i % p][j % q] for i in range(n) for j in range(m)):
                    continue
                for r in range(n - p + 1):
                    for c in range(m - q + 1):
                        best = min(best, (p + 1) * (q + 1) * max(costs[i][j] for i in range(r, r + p) for j in range(c, c + q)))
        run(16638, f'{n} {m}\n' + '\n'.join(colors) + '\n' + '\n'.join(' '.join(map(str, row)) for row in costs), best)
        words = []
        while len(words) < 6:
            s = ''.join(RNG.choice('abc') for j in range(RNG.randint(1, 4)))
            if s not in words:
                words.append(s)
        winners = set()
        for alphabet in itertools.permutations('abc'):
            rank = {c: i for i, c in enumerate(alphabet)}
            winners.add(min(range(len(words)), key=lambda i: tuple(rank[c] for c in words[i])))
        expected = str(len(winners)) + '\n' + '\n'.join(s for i, s in enumerate(words) if i in winners)
        run(15049, str(len(words)) + '\n' + '\n'.join(words), expected)


def palindromes():
    for _ in range(50):
        s = ''.join(RNG.choice('abc') for j in range(RNG.randint(2, 13)))
        pals = [(l, r) for l in range(len(s)) for r in range(l + 1, len(s) + 1) if s[l:r] == s[l:r][::-1]]
        run(236738, s, sum(len(set(s[l:r])) for l, r in pals))
        expected = max((b - a + d - c for a, b in pals for c, d in pals if b == c), default=0)
        run(236545, s, expected)
        lengths = sorted((r - l for l, r in pals if (r - l) % 2), reverse=True)
        k = RNG.randint(1, len(s) ** 2)
        answer = -1
        if k <= len(lengths):
            answer = 1
            for value in lengths[:k]:
                answer = answer * value % 19930726
        run(236544, f'{len(s)} {k}\n{s}', answer)
        binary = ''.join(RNG.choice('01') for j in range(len(s)))
        expected = sum(all(binary[l + i] != binary[r - 1 - i] for i in range(r - l))
                       for l in range(len(s)) for r in range(l + 1, len(s) + 1))
        run(236735, str(len(binary)) + '\n' + binary, expected)


def border(s, k):
    for length in range(len(s), 0, -1):
        candidate = s[:length]
        if s.endswith(candidate) and sum(s[i:i + length] == candidate for i in range(len(s) - length + 1)) >= k:
            return length
    return -1


def changing_prefixes_and_xor():
    for _ in range(40):
        original = ''.join(RNG.choice('ab') for j in range(RNG.randint(1, 8)))
        s, operations, answers = original, [], []
        for j in range(45):
            if RNG.randrange(3) == 0:
                c = RNG.choice('ab')
                s += c
                operations.append('1 ' + c)
            else:
                k = RNG.randint(1, len(s) + 3)
                operations.append('2 ' + str(k))
                answers.append(str(border(s, k)))
        run(233500, f'{len(original)} {len(operations)}\n' + original + '\n' + '\n'.join(operations), '\n'.join(answers))
        k = RNG.randint(1, len(s))
        answer = border(s, k)
        run(233499, f'{len(s)} {k}\n{s}', '-1' if answer == -1 else s[:answer])
        a = [RNG.randint(0, 63) for j in range(RNG.randint(1, 15))]
        candidates = []
        for l in range(len(a)):
            value = 0
            for r in range(l, len(a)):
                value ^= a[r]
                candidates.append((value, -(r + 1), -(r - l + 1), l + 1, r + 1))
        best = max(candidates)
        run(22998, str(len(a)) + '\n' + '\n'.join(map(str, a)), f'{best[0]} {best[3]} {best[4]}')


if __name__ == '__main__':
    periods_and_lexicography()
    palindromes()
    changing_prefixes_and_xor()
    ledger = read(CONTENT / 'reviewed.json')
    report = {'passed': True, 'randomSeed': 2026110807, 'fixtures': sum(COUNTS.values()),
              'problems': {k: {'fixtures': v, 'programSha256': ledger['nowcoder-global::' + k]['programSha256']}
                           for k, v in COUNTS.items()}}
    write(OUT / 'strings-independent-validation.json', report)
    print(report)
