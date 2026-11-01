"""Honor P8201's explicitly case-insensitive Yes/No output rule."""
def path_value_verdicts(inp,got,expected=None):
    try:
        header=inp.split('\n',1)[0].split();queries=int(header[1])
        actual=[s.casefold() for s in got.split()]
        wanted=[s.casefold() for s in str(expected).split()]
        assert len(actual)==len(wanted)==queries,'One verdict is required per query'
        assert all(s in {'yes','no'} for s in actual),'Unknown verdict'
        assert actual==wanted,'A path-existence verdict differs from the oracle'
        return True
    except (ValueError,IndexError,AssertionError) as error:return False,str(error)

def selftest():
    inp='2 2\n0 0\n1 2\n1 2 0\n1 2 1\n'
    assert path_value_verdicts(inp,'yES nO','Yes No') is True
    for invalid in ['Yes','Yes No Yes','Yes Yes','No No','Yes maybe','1 0','']:
        assert path_value_verdicts(inp,invalid,'Yes No')[0] is False

if __name__=='__main__':
    selftest();print('Case-insensitive path verdicts accept legal spellings and reject wrong, missing or extra answers.')
