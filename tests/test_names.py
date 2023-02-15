from unittest import TestCase

from lapidary.runtime.names import escape_name, get_enum_field_name


class MangleNamesTest(TestCase):
    def test__mangle_name_equal(self):
        self.assertEqual('a', escape_name('a'))

    def test__mangle_name_mangled_colon(self):
        self.assertEqual('u_00003a', escape_name(':'))

    def test__mangle_name_mangled_mixed(self):
        self.assertEqual('au_00003ab', escape_name('a:b'))

    def test__mangle_name_mangled_escape_seq(self):
        self.assertEqual('auu_00005fb', escape_name('au_b'))


class EnumFieldNamesTests(TestCase):
    def test_none_value(self):
        with self.assertRaises(ValueError):
            get_enum_field_name(None)

    def test_blank_value(self):
        with self.assertRaises(ValueError):
            get_enum_field_name("")

    def test_str_name_value(self):
        self.assertEqual("valid_name", get_enum_field_name("valid_name"))

    def test_str_invalid_name_value(self):
        self.assertEqual("invalidu_000020name", get_enum_field_name("invalid name"))

    def test_int_value(self):
        self.assertEqual("u_000033", get_enum_field_name(3))

    def test_float_value(self):
        self.assertEqual("u_000030u_00002e3", get_enum_field_name(.3))

