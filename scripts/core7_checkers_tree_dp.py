"""Compare sabotage limits against exact rational literal-closure oracles."""
from fractions import Fraction


def critical_fraction(inp,got,expected=None):
    try:
        tokens=got.split()
        assert len(tokens)==1,'Expected one real value'
        value=Fraction(tokens[0]);target=Fraction(str(expected).strip())
        assert 0<=value<=1,'Proportion outside [0,1]'
        assert abs(value-target)<Fraction(1,1000000),'Critical value differs by at least 1e-6'
        return True
    except (ValueError,ZeroDivisionError,AssertionError,TypeError) as e:return False,str(e)


def selftest():
    assert critical_fraction('', '0.6666666667\n','2/3') is True
    assert critical_fraction('', '0.0000020000\n','1/499999') is True
    for wrong in ['nan','inf','0.66660','-0.1','1.1','0.66 0.67']:
        assert critical_fraction('',wrong,'2/3')[0] is False


if __name__=='__main__':
    selftest()
    print('Critical-value checker rejects malformed, out-of-range and inaccurate output.')
