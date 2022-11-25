from unittest import TestCase

from lapidary.runtime.names import _mangle_name


class NamesTest(TestCase):
    def test__mangle_name_equal(self):
        self.assertEqual('a', _mangle_name('a'))

    def test__mangle_name_mangled_colon(self):
        self.assertEqual('u_00003a', _mangle_name(':'))

    def test__mangle_name_mangled_mixed(self):
        self.assertEqual('au_00003ab', _mangle_name('a:b'))

    def test__mangle_name_mangled_escape_seq(self):
        self.assertEqual('auu_00005fb', _mangle_name('au_b'))
