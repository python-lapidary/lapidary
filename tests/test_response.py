import unittest

from lapidary.runtime.response import _status_code_matches


class MyTestCase(unittest.TestCase):
    def test__status_code_matches(self):
        matches = [m for m in _status_code_matches('400')]
        self.assertEqual(['400', '40X', '4XX', 'default'], matches)
