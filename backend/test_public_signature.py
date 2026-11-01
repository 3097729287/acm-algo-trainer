"""Public digest detects nested changes, including those made between reads."""
import copy
import json
import unittest

from public_signature import digest


class PublicSignatureTests(unittest.TestCase):
    def test_json_round_trip_and_object_sharing_are_equivalent(self):
        shared={'title':'重复 title','values':[1,2,3,None,True,False,1.5]}
        value=[shared,shared,{'same':shared['title']}]
        self.assertEqual(digest(value),digest(json.loads(json.dumps(value))))
        self.assertEqual(digest(value),digest(copy.deepcopy(value)))

    def test_nested_row_rating_settings_and_dates_all_affect_digest(self):
        inputs=[{'A':{'title':'fixture','tags':['dp']}},{'url':{'difficulty':1500}},0,10000,
                {'Contest':{'startedAt':'2026-10-01'}},{'url':{'endedAt':'2026-10-02'}}]
        before=digest(inputs)
        for index in range(6):
            changed=copy.deepcopy(inputs)
            if isinstance(changed[index],dict):changed[index]['nested-change']={'more':[42]}
            else:changed[index]+=1
            self.assertNotEqual(digest(changed),before)
        inputs[0]['A']['tags'].append('greedy')
        self.assertNotEqual(digest(inputs),before)
        self.assertNotEqual(digest([1]),digest(['1']))
        self.assertNotEqual(digest([1]),digest([True]))


if __name__=='__main__':unittest.main()
