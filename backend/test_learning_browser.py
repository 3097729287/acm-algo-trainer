"""Real HTTP persistence boundaries for many independent learning drafts."""
import http.client
import json
import unittest
import test_backend as fixtures


class LearningBrowserHTTPTests(unittest.TestCase):
    setUp=fixtures.BackendTests.setUp
    tearDown=fixtures.BackendTests.tearDown
    request=fixtures.BackendTests.request

    def test_many_template_drafts_roundtrip_without_widening_other_write_endpoints(self):
        tabs=[dict(kind='template',id='new-'+str(i),title='draft '+str(i),
                   visit={'draft':{'title':'draft '+str(i),'code':'x'*6000}},state={},scroll=[]) for i in range(64)]
        value={'learningPaths':{'browserV1':{'version':1,'tabs':tabs,'active':'template:new-63','open':True}}}
        self.assertGreater(len(json.dumps(value)),262144)
        self.assertEqual(self.request('/api/preferences',{'preferences':value})[0],200)
        self.assertEqual(self.request('/api/preferences')[1]['preferences'],value)
        self.assertEqual(self.request('/api/preferences',{'preferences':{'favorites':['x'*150000]}})[0],400)
        self.assertEqual(self.declared('/api/draft',300000),400)
        self.assertEqual(self.request('/api/preferences',{'preferences':{}},{'X-TB-Token':'invalid'})[0],403)

    def test_preferences_still_reject_oversized_declared_bodies_without_reading_them(self):
        self.assertEqual(self.declared('/api/preferences',48*1024*1024+1),400)

    def declared(self,path,size):
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        connection.putrequest('POST',path)
        connection.putheader('Content-Type','application/json')
        connection.putheader('X-TB-Token',self.server.store.token)
        connection.putheader('Content-Length',str(size))
        connection.endheaders()
        response=connection.getresponse()
        status=response.status;response.read();connection.close();return status


if __name__=='__main__':unittest.main()
