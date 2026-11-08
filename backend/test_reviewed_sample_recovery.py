"""Never treat arbitrary old examples as replaceable attachment placeholders."""
import copy
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reviewed_original_apply',ROOT/'scripts/apply_reviewed_statement_recovery_20261109.py')
recovery=importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class ReviewedSampleRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory(prefix='tb-reviewed-sample-')
        self.addCleanup(self.directory.cleanup)
        self.source=Path(self.directory.name)
        (self.source/'statement-assets').mkdir()
        self.input=b'2\r\n1 3\r\n'
        self.output=b'4\r\n'
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            archive.writestr('sample/sample.in',self.input)
            archive.writestr('sample/sample.out',self.output)
        raw=stream.getvalue();self.digest=hashlib.sha256(raw).hexdigest()
        (self.source/'statement-assets'/(self.digest+'.bin')).write_bytes(raw)
        self.old={'samples':[{'input':'见附件','output':'见附件'}]}
        self.incoming={'samples':[{'input':self.input.decode(),'output':self.output.decode()}],
                       'attachments':{'https://example.invalid/official.zip':{'sha256':self.digest,'mime':'application/zip'}}}
        self.proof={'attachmentSampleReplacements':[{'oldSample':{'input':'见附件','output':'见附件'},
            'attachmentSha256':self.digest,'inputFile':'sample/sample.in','outputFile':'sample/sample.out',
            'inputSha256':hashlib.sha256(self.input).hexdigest(),'outputSha256':hashlib.sha256(self.output).hexdigest()}]}

    def test_exact_offline_zip_replaces_only_the_literal_placeholder(self):
        recovery.assert_samples_preserved(self.old,self.incoming,self.proof,self.source)

    def test_placeholder_cannot_disappear_without_archived_evidence(self):
        with self.assertRaises(AssertionError):recovery.assert_samples_preserved(self.old,self.incoming,{},self.source)

    def test_wrong_archive_content_or_digest_is_rejected(self):
        incoming=copy.deepcopy(self.incoming)
        incoming['samples'][0]['output']='5\r\n'
        with self.assertRaises(AssertionError):recovery.assert_samples_preserved(self.old,incoming,self.proof,self.source)
        proof=copy.deepcopy(self.proof)
        proof['attachmentSampleReplacements'][0]['outputSha256']='0'*64
        with self.assertRaises(AssertionError):recovery.assert_samples_preserved(self.old,self.incoming,proof,self.source)

    def test_an_actual_old_example_cannot_be_excused_as_a_placeholder(self):
        old=copy.deepcopy(self.old);old['samples'].append({'input':'real input','output':'real output'})
        with self.assertRaises(AssertionError):recovery.assert_samples_preserved(old,self.incoming,self.proof,self.source)
        proof=copy.deepcopy(self.proof);proof['attachmentSampleReplacements'][0]['oldSample']={'input':'real input','output':'real output'}
        with self.assertRaises(AssertionError):recovery.assert_samples_preserved(old,self.incoming,proof,self.source)

    def test_existing_ordinary_samples_need_no_replacement_exception(self):
        old={'samples':[{'input':'2\n1 3','output':'4'}]}
        recovery.assert_samples_preserved(old,self.incoming,{},self.source)


if __name__=='__main__':unittest.main()
