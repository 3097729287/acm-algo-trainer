"""Exact rational targets and required six-place finite decimal output."""
from fractions import Fraction
import re


def reward_fraction(inp,got,expected=None):
    try:
        assert re.fullmatch(r'-?\d+\.\d{6}\s*',got),'Expected one value with exactly six decimal places'
        value=Fraction(got.strip());target=Fraction(str(expected).strip())
        assert value>=0,'Skipping every item is always feasible'
        assert abs(value-target)<Fraction(1,1000000),'Expected score differs by at least 1e-6'
        return True
    except (ValueError,ZeroDivisionError,AssertionError,TypeError) as e:return False,str(e)


def selftest():
    assert reward_fraction('', '0.333333\n','1/3') is True
    assert reward_fraction('', '100000000.000000\n','100000000') is True
    for wrong in ['nan','inf','0.33333','0.333333 0.333333','0.333330','-0.333333']:
        assert reward_fraction('',wrong,'1/3')[0] is False


if __name__=='__main__':selftest();print('Finite six-place reward output is checked against exact rational targets.')
