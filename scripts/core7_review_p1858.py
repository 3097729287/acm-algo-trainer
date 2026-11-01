"""Only review feasible-list counts; do not invent an unspecified output rule."""
import json
from core7_authoring import OUT


def literal_lists(capacity,items):
    values=[]
    for mask in range(1<<len(items)):
        weight=sum(w for i,(w,v) in enumerate(items) if mask>>i&1)
        if weight==capacity:values.append(sum(v for i,(w,v) in enumerate(items) if mask>>i&1))
    return sorted(values,reverse=True)


def main():
    assert literal_lists(1,[(1,1)])==[1]
    assert len(literal_lists(1,[(1,1)]))<2
    assert literal_lists(1,[(1,5),(1,5)])==[5,5]
    result={'casesPassed':2,'insufficientListsHasNoSpecifiedOutput':True,
            'equalValueListsRemainDistinct':True,'fullSolutionVerified':False}
    (OUT/'p1858-semantic-review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
