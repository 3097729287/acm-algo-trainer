"""An integer-preserving evaluator for the short NC50999 expression grammar."""
from nowcoder_editorials import CONTENT, read, register


def run():
    if 'nowcoder-global::50999' in read(CONTENT / 'reviewed.json'):
        return
    code = r'''import sys


def remove_unmatched_parentheses(source):
    stack = []
    matched = set()
    for i, char in enumerate(source):
        if char == '(':
            stack.append(i)
        elif char == ')' and stack:
            matched.add(stack.pop())
            matched.add(i)
    return ''.join(char for i, char in enumerate(source) if char not in '()' or i in matched)


def divide(a, b):
    quotient = abs(a) // abs(b)
    return -quotient if (a < 0) != (b < 0) else quotient


class Parser:
    def __init__(self, source):
        self.source = source
        self.pos = 0

    def atom(self):
        if self.source[self.pos] in '+-':
            sign = self.source[self.pos]
            self.pos += 1
            value = self.atom()
            return value if sign == '+' else -value
        if self.source[self.pos] == '(':
            self.pos += 1
            value = self.expression()
            self.pos += 1
            return value
        value = 0
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            value = value * 10 + int(self.source[self.pos])
            self.pos += 1
        return value

    def power(self):
        value = self.atom()
        while self.pos < len(self.source) and self.source[self.pos] == '^':
            self.pos += 1
            exponent = self.atom()
            if exponent < 0:
                if value == 1:
                    value = 1
                elif value == -1:
                    value = -1 if exponent % 2 else 1
                else:
                    value = 0
            else:
                value = pow(value, exponent)
        return value

    def term(self):
        value = self.power()
        while self.pos < len(self.source) and self.source[self.pos] in '*/':
            op = self.source[self.pos]
            self.pos += 1
            right = self.power()
            value = value * right if op == '*' else divide(value, right)
        return value

    def expression(self):
        value = self.term()
        while self.pos < len(self.source) and self.source[self.pos] in '+-':
            op = self.source[self.pos]
            self.pos += 1
            right = self.term()
            value = value + right if op == '+' else value - right
        return value


def main():
    source = remove_unmatched_parentheses(sys.stdin.readline().strip())
    print(Parser(source).expression())


if __name__ == '__main__':
    main()
'''
    meaning = '计算带加减乘整除和乘方的短表达式，支持负数、括号以及题目提到的多余括号。'
    idea = ('先用括号栈配对，删除没有匹配对象的额外括号。然后按优先级写四层递归下降：'
            '表达式处理加减，项处理乘除，幂处理乘方，原子处理整数、符号和括号。'
            '每一层用循环依次合并同级运算，采用该原题公开参考实现使用的从左到右顺序。'
            '整数除法用绝对值整除后恢复符号，保持向零截断。Python 整数保存精确中间值，'
            '即使两个很大的幂最后相减得到小结果，也不会先溢出。')
    markdown = ('## 表达式计算4\n\n### 题意\n\n' + meaning + '\n\n### 思路\n\n' + idea +
                '\n\n### 参考代码\n\n```python\n' + code + '```\n\n### 复杂度\n\n'
                '语法扫描与递归调用数为 $O(L)$，其中 $L≤30$。整数算术还需计入实际中间值位数的运算成本；递归和语法存储为 $O(L)$。\n\n'
                '### 易错点\n\nPython 的 // 对负数向下取整，题目整除应向零截断，所以单独实现 divide。'
                '乘方优先级高于乘除，配对的括号内部要完整递归。不要直接用 eval 解释原串，原题的额外括号和同级乘方规则需要明确处理。\n')
    register(50999, 1800, ['表达式', '递归下降'], idea, {'default': markdown},
             cases=[{'input': '(-5)^2))))+2', 'output': '27'}, {'input': '2+2^4/8-6', 'output': '-2'},
                    {'input': '3+(2*5+7^2)-6*(3+2)', 'output': '32'}, {'input': '2^3^2', 'output': '64'},
                    {'input': '(-7)/3', 'output': '-2'}, {'input': '2^100-2^100+1', 'output': '1'}])


if __name__ == '__main__':
    run()
    print('Registered the precise short-expression evaluator.')
