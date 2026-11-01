"""Validate minimal balanced supersequences, preserving empty test cases."""


def bracket_inputs(inp):
    lines=inp.replace('\r\n','\n').split('\n');tests=int(lines[0]);assert lines[1]==''
    strings=[];at=2
    for case in range(tests):
        strings.append(lines[at] if at<len(lines) else '');at+=1
        if case+1<tests:assert lines[at]=='';at+=1
    return strings


def bracket_supersequence(inp,got,expected=None):
    try:
        strings=bracket_inputs(inp);lines=got.replace('\r\n','\n').split('\n');tests=len(strings)
        if set(str(expected).strip())<={'(',')','[',']'}:
            assert tests==1;lengths=[len(str(expected).strip())]
        else:lengths=list(map(int,str(expected).split()))
        assert len(lengths)==tests,'Expected lengths missing'
        assert len(lines)>=2*tests-1,'Missing output case, including empty case'
        assert all(not line.strip() for line in lines[2*tests-1:]),'Extra nonempty output'
        for i,(s,target) in enumerate(zip(strings,lengths)):
            if i:assert not lines[2*i-1].strip(),'Expected blank output separator'
            word=lines[2*i].strip();stack=[]
            for c in word:
                if c in '([':stack.append(c)
                else:
                    assert c in ')]' and stack,'Not balanced'
                    assert (stack.pop(),c) in [('(',')'),('[',']')],'Mismatched bracket types'
            assert not stack,'Unclosed bracket'
            at=0
            for c in word:
                if at<len(s) and s[at]==c:at+=1
            assert at==len(s),'Original sequence is not a subsequence'
            assert len(word)==target,'Balanced sequence is not shortest'
        return True
    except (AssertionError,ValueError,TypeError,IndexError) as e:return False,str(e)


def selftest():
    inp='1\n\n([(]\n'
    assert bracket_supersequence(inp,'()[()]\n','()[()]\n\n') is True
    for wrong in ['([)]\n','()([])[]\n','([])\n']:
        assert bracket_supersequence(inp,wrong,'6')[0] is False
    inp='2\n\n\n\n(\n'
    assert bracket_supersequence(inp,'\n\n()\n','0\n2') is True
    assert bracket_supersequence(inp,'()\n\n','0\n2')[0] is False


if __name__=='__main__':selftest();print('Bracket checker validates optimality, types, subsequences and empty cases.')
