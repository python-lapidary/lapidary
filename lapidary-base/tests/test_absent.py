import unittest

from lapidary_base import Absent, ABSENT


class MyTestCase(unittest.TestCase):
    def test_new(self):
        a = Absent()
        self.assertTrue(a is ABSENT)

    def test_pickle_clone(self):
        import pickle

        data = pickle.dumps(ABSENT)
        clone = pickle.loads(data)

        self.assertTrue(clone is ABSENT)
