import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib._calc import CalcEngine


class TestSafeEval(unittest.TestCase):
    def setUp(self):
        self.calc = CalcEngine()

    def test_complex_expression(self):
        self.assertEqual(self.calc.safe_eval("(10+100)*20*(50/10)"), 11000)

    def test_true_division_truncates(self):
        self.assertEqual(self.calc.safe_eval("7/2"), 3)

    def test_nested_parens(self):
        self.assertEqual(self.calc.safe_eval("(2+3)*4"), 20)

    def test_negative_intermediate_ok(self):
        self.assertEqual(self.calc.safe_eval("(5-3)*10"), 20)

    def test_zero(self):
        self.assertEqual(self.calc.safe_eval("0"), 0)

    def test_max_u64(self):
        self.assertEqual(self.calc.safe_eval("18446744073709551615"), 2 ** 64 - 1)

    def test_overflow_raises(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("18446744073709551616")

    def test_negative_result_raises(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("5-10")

    def test_negative_float_result_raises(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("1/3 - 1")

    def test_name_rejected(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("a+1")

    def test_call_rejected(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("__import__('os')")

    def test_pow_rejected(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("2**8")

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("")

    def test_divzero_rejected(self):
        with self.assertRaises(ValueError):
            self.calc.safe_eval("1/0")


if __name__ == '__main__':
    unittest.main()
