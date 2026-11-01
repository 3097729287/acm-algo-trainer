"""Stable-identity content integration must preserve independent source edits."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('delivered_contests',Path(__file__).resolve().parents[1]/'scripts/integrate_delivered_contests.py')
integration=importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration)


class DeliveredContentIntegrationTests(unittest.TestCase):
    def test_additions_keep_existing_editorials_images_order_and_other_revisions(self):
        old={'problem_id':'old','markdown':'original','images':{'figure':'image'}}
        revised={**old,'markdown':'independently reviewed'}
        new={'problem_id':'new','markdown':'delivered','images':{'new-figure':'new-image'}}
        merged,changed=integration.merge_rows([old],[revised],[old,new],'solutions.json')
        self.assertEqual(merged,[revised,new])
        self.assertEqual(changed,[('new',)])
        self.assertEqual(integration.merge_rows([old],merged,[old,new],'solutions.json')[0],merged)

    def test_separate_metadata_fields_merge_without_losing_either_revision(self):
        base=[{'id':'one','raw':{'title':'before','source':'official'}}]
        ours=[{'id':'one','raw':{'title':'before','source':'official','review':'verified'}}]
        theirs=[{'id':'one','raw':{'title':'corrected','source':'official'}}]
        merged,_=integration.merge_rows(base,ours,theirs,'problems.json')
        self.assertEqual(merged,[{'id':'one','raw':{'title':'corrected','source':'official','review':'verified'}}])

    def test_conflicting_prose_and_delivered_deletion_stop_without_mutating_inputs(self):
        base=[{'problem_id':'one','markdown':'original'}]
        ours=[{'problem_id':'one','markdown':'current reviewed'}]
        theirs=[{'problem_id':'one','markdown':'different incoming'}]
        with self.assertRaisesRegex(ValueError,'Concurrent content conflict'):
            integration.merge_rows(base,ours,theirs,'solutions.json')
        with self.assertRaisesRegex(ValueError,'remove a record'):
            integration.merge_rows(base,ours,[],'solutions.json')
        self.assertEqual(ours,[{'problem_id':'one','markdown':'current reviewed'}])

    def test_composite_lecture_relationships_are_distinct_and_duplicates_rejected(self):
        first={'problem_id':'one','lecture_id':'foundation','kind':'own','position':0}
        second={**first,'lecture_id':'different-foundation','kind':'explicit','position':1}
        self.assertEqual(integration.merge_rows([first],[first],[first,second],'links.json')[0],[first,second])
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            integration.merge_rows([first],[first,{**first,'kind':'explicit'}],[first,second],'links.json')


if __name__=='__main__':unittest.main()
