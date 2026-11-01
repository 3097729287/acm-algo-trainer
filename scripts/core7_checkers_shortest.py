"""Compare geometric/expected-time values under the original error rule."""
from decimal import Decimal,InvalidOperation,localcontext


def path_decimal(inp,got,expected=None):
    try:
        if len(got.split())!=1:return False,'Expected exactly one numeric result'
        with localcontext() as context:
            context.prec=65
            actual,wanted=Decimal(got.strip()),Decimal(str(expected).strip())
            if not actual.is_finite() or not wanted.is_finite():return False,'Non-finite result'
            tolerance=Decimal('1e-9')*max(Decimal(1),abs(wanted))
            return abs(actual-wanted)<=tolerance,f'Expected {wanted}, received {actual}'
    except (InvalidOperation,ValueError,TypeError):return False,'Malformed numeric result'
