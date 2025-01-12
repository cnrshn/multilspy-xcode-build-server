import unittest
from multispy_xcode_build_server.server import XcodeBuildServer

class TestXcodeBuildServer(unittest.TestCase):
    def setUp(self):
        self.server = XcodeBuildServer()

    def test_initialization(self):
        self.assertFalse(self.server.initialized)
        self.server.initialize()
        self.assertTrue(self.server.initialized) 