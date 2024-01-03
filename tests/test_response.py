import unittest

from lapidary.runtime.response import _status_code_matches


class MatchResponseCodeTest(unittest.TestCase):
    def test__status_code_matches(self):
        matches = list(_status_code_matches('400'))
        self.assertEqual(['400', '4XX', 'default'], matches)
