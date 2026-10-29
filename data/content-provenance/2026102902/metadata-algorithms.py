"""Independent local reference implementations; never submit to an OJ."""
from math import gcd


def solve(task, text):
    tokens = text.split()
    ints = lambda: list(map(int, tokens))
    if task == 'agc001_a':
        a = ints()
        return str(sum(sorted(a[1:])[::2]))
    if task == 'agc002_a':
        a, b = ints()
        if a <= 0 <= b:
            return 'Zero'
        return 'Positive' if a > 0 or (b - a + 1) % 2 == 0 else 'Negative'
    if task == 'agc003_a':
        s = tokens[0]
        return 'Yes' if (('N' in s) == ('S' in s) and ('E' in s) == ('W' in s)) else 'No'
    if task == 'agc004_a':
        a, b, c = ints()
        return str(0 if any(x % 2 == 0 for x in (a, b, c)) else min(a*b, a*c, b*c))
    if task == 'agc006_a':
        n = int(tokens[0])
        s, t = tokens[1:]
        k = max(k for k in range(n + 1) if not k or s[-k:] == t[:k])
        return str(2 * n - k)
    if task == 'agc007_a':
        h, w = map(int, tokens[:2])
        return 'Possible' if sum(row.count('#') for row in tokens[2:]) == h + w - 1 else 'Impossible'
    if task == 'agc008_a':
        x, y = ints()
        candidates = []
        for start_flip in range(2):
            for end_flip in range(2):
                start = -x if start_flip else x
                target = -y if end_flip else y
                if target >= start:
                    candidates.append(target - start + start_flip + end_flip)
        return str(min(candidates))
    if task == 'agc009_a':
        data = ints()
        pairs = list(zip(data[1::2], data[2::2]))
        added = 0
        for a, b in reversed(pairs):
            added += (-(a + added)) % b
        return str(added)
    if task == 'agc010_a':
        return 'YES' if sum(x % 2 for x in ints()[1:]) % 2 == 0 else 'NO'
    if task == 'agc011_a':
        n, c, k, *arrival = ints()
        arrival.sort()
        buses, i = 0, 0
        while i < n:
            first = i
            while i < n and i - first < c and arrival[i] <= arrival[first] + k:
                i += 1
            buses += 1
        return str(buses)
    if task == 'agc012_a':
        n, *a = ints()
        a.sort()
        return str(sum(a[n::2]))
    if task == 'agc013_a':
        n, *a = ints()
        segments, direction = 1, 0
        for i in range(1, n):
            d = (a[i] > a[i-1]) - (a[i] < a[i-1])
            if d and direction and d != direction:
                segments += 1
                direction = 0
            elif d:
                direction = d
        return str(segments)
    if task == 'agc014_a':
        a, b, c = ints()
        if a == b == c and a % 2 == 0:
            return '-1'
        count = 0
        while a % 2 == b % 2 == c % 2 == 0:
            a, b, c = (b+c)//2, (a+c)//2, (a+b)//2
            count += 1
        return str(count)
    if task == 'agc015_a':
        n, a, b = ints()
        if a > b or (n == 1 and a != b):
            return '0'
        return str(1 if n == 1 else (n-2)*(b-a)+1)
    if task == 'agc019_a':
        q, h, s, d, n = ints()
        unit = min(4*q, 2*h, s)
        double = min(2*unit, d)
        return str((n//2)*double + (n % 2)*unit)
    if task == 'agc020_a':
        n, a, b = ints()
        return 'Alice' if (b-a) % 2 == 0 else 'Borys'
    if task == 'agc021_a':
        s = tokens[0]
        best = sum(map(int, s))
        for i, ch in enumerate(s):
            if ch != '0':
                best = max(best, sum(map(int, s[:i])) + int(ch)-1 + 9*(len(s)-1-i))
        return str(best)
    if task == 'agc024_a':
        a, b, c, k = ints()
        return str((a-b) * (-1 if k % 2 else 1))
    if task == 'agc025_a':
        n = int(tokens[0])
        digit_sum = lambda x: sum(map(int, str(x)))
        return str(min(digit_sum(a) + digit_sum(n-a) for a in range(1, n)))
    if task == 'agc026_a':
        n, *a = ints()
        changes = run = 0
        previous = None
        for value in a:
            if value != previous:
                changes += run // 2
                run = 0
            run += 1
            previous = value
        return str(changes + run//2)
    if task == 'agc027_a':
        n, budget, *a = ints()
        a.sort()
        happy = 0
        for amount in a:
            if budget < amount:
                break
            happy += 1
            budget -= amount
        if happy == n and budget:
            happy -= 1
        return str(happy)
    if task == 'agc029_a':
        black = total = 0
        for ch in tokens[0]:
            if ch == 'B':
                black += 1
            else:
                total += black
        return str(total)
    if task == 'agc040_a':
        s = tokens[0]
        values = [0] * (len(s)+1)
        for i, ch in enumerate(s):
            if ch == '<':
                values[i+1] = values[i] + 1
        for i in range(len(s)-1, -1, -1):
            if s[i] == '>':
                values[i] = max(values[i], values[i+1]+1)
        return str(sum(values))
    if task == 'agc046_a':
        return str(360 // gcd(360, int(tokens[0])))
    raise KeyError(task)


if __name__ == '__main__':
    import sys
    print(solve(sys.argv[1], sys.stdin.read()))
