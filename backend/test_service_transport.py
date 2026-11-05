import ssl
import unittest
from unittest.mock import Mock,patch
from urllib.error import HTTPError,URLError
from urllib.request import Request
from leaderboard import AdaptiveServiceOpener,service_opener,NoRedirect

class ServiceTransportTests(unittest.TestCase):
    def setUp(self):
        AdaptiveServiceOpener.routes.clear()
        self.direct,self.system=Mock(),Mock()
        self.opener=AdaptiveServiceOpener('official.test',self.direct,self.system)

    def test_safe_get_recovers_and_shares_the_successful_route(self):
        self.direct.open.side_effect=URLError(TimeoutError())
        response=self.opener.open(Request('https://official.test/v2/accounts/state'),timeout=12)
        self.assertIs(response,self.system.open.return_value)
        self.assertEqual(self.direct.open.call_args.kwargs['timeout'],3)
        self.assertLessEqual(self.system.open.call_args.kwargs['timeout'],12)
        self.direct.open.reset_mock()
        another=AdaptiveServiceOpener('official.test',self.direct,self.system)
        another.open(Request('https://official.test/v1/profile',data=b'{}',method='PUT'),timeout=8)
        self.direct.open.assert_not_called()
        self.assertEqual(self.system.open.call_count,2)

    def test_mutations_are_never_retried(self):
        self.direct.open.side_effect=URLError(TimeoutError())
        for method in ['POST','PUT','DELETE']:
            with self.assertRaises(URLError):self.opener.open(Request('https://official.test/v1/action',data=b'{}',method=method),timeout=8)
        self.system.open.assert_not_called()

    def test_authorization_certificate_and_redirect_errors_do_not_switch_routes(self):
        for issue in [HTTPError('https://official.test',401,'unauthorized',{},None),URLError(ssl.SSLCertVerificationError()),URLError('redirect rejected')]:
            self.direct.open.side_effect=issue
            with self.assertRaises((HTTPError,URLError)):self.opener.open(Request('https://official.test/v1/accounts/me'),timeout=8)
        self.system.open.assert_not_called()

    def test_system_route_can_fall_back_to_direct_when_proxy_stops(self):
        AdaptiveServiceOpener.routes['official.test']=True
        self.system.open.side_effect=URLError(ConnectionRefusedError())
        self.assertIs(self.opener.open(Request('https://official.test/v1/accounts/me'),timeout=8),self.direct.open.return_value)
        self.assertFalse(AdaptiveServiceOpener.routes['official.test'])

    def test_no_second_attempt_after_deadline(self):
        self.direct.open.side_effect=URLError(TimeoutError())
        with patch('leaderboard.time.monotonic',side_effect=[1,10]):
            with self.assertRaises(URLError):self.opener.open(Request('https://official.test/v1/accounts/me'),timeout=8)
        self.system.open.assert_not_called()

    def test_custom_and_loopback_services_keep_their_existing_routing(self):
        with patch('leaderboard.bundled_endpoint',return_value='https://official.test'),patch('leaderboard.getproxies',return_value={'https':'http://127.0.0.1:7890'}):
            self.assertIsInstance(service_opener('https://official.test'),AdaptiveServiceOpener)
            self.assertNotIsInstance(service_opener('http://127.0.0.1:1234'),AdaptiveServiceOpener)
            self.assertNotIsInstance(service_opener('https://custom.test'),AdaptiveServiceOpener)

if __name__=='__main__':unittest.main()
