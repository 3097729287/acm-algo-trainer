import os
import socket
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from backend import LocalServer


@unittest.skipUnless(os.name == 'nt', 'Windows socket reuse semantics')
class ExclusivePortTests(unittest.TestCase):
    def test_other_version_cannot_share_our_port(self):
        with LocalServer(('127.0.0.1', 0), BaseHTTPRequestHandler) as server:
            with socket.socket() as old:
                old.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                with self.assertRaises(OSError):
                    old.bind(server.server_address)

    def test_do_not_share_an_already_running_legacy_port(self):
        with ThreadingHTTPServer(('127.0.0.1', 0), BaseHTTPRequestHandler) as old:
            with self.assertRaises(OSError):
                LocalServer(old.server_address, BaseHTTPRequestHandler)
