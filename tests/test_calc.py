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


class TestUnitToBytes(unittest.TestCase):
    def setUp(self):
        self.calc = CalcEngine()

    def test_mb(self):
        self.assertEqual(self.calc.unit_to_bytes(4, 'MB'), 4194304)

    def test_kb(self):
        self.assertEqual(self.calc.unit_to_bytes(1, 'KB'), 1024)

    def test_zero(self):
        self.assertEqual(self.calc.unit_to_bytes(0, 'B'), 0)

    def test_fraction_kb(self):
        self.assertEqual(self.calc.unit_to_bytes(0.5, 'KB'), 512)

    def test_gb(self):
        self.assertEqual(self.calc.unit_to_bytes(1, 'GB'), 1073741824)

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            self.calc.unit_to_bytes(1, 'PB')

    def test_overflow(self):
        with self.assertRaises(ValueError):
            self.calc.unit_to_bytes(10 ** 20, 'B')

    def test_bad_value(self):
        with self.assertRaises(ValueError):
            self.calc.unit_to_bytes("abc", 'MB')

    def test_negative_value(self):
        with self.assertRaises(ValueError):
            self.calc.unit_to_bytes(-1, 'KB')

    def test_inf_value(self):
        with self.assertRaises(ValueError):
            self.calc.unit_to_bytes(float('inf'), 'GB')


class TestBytesToUnits(unittest.TestCase):
    def setUp(self):
        self.calc = CalcEngine()

    def test_b(self):
        u = self.calc.bytes_to_units(4194304)
        self.assertEqual(u['B'], '4194304')

    def test_kb_mb(self):
        u = self.calc.bytes_to_units(4194304)
        self.assertEqual(float(u['KB']), 4096)
        self.assertEqual(float(u['MB']), 4)

    def test_keys(self):
        u = self.calc.bytes_to_units(0)
        self.assertEqual(set(u.keys()), {'B', 'KB', 'MB', 'GB', 'TB'})
        self.assertEqual(u['B'], '0')

    def test_exact_fraction(self):
        # 512 字节 = 0.5 KB，应输出精确小数而非科学计数
        u = self.calc.bytes_to_units(512)
        self.assertEqual(u['KB'], '0.5')

    def test_no_scientific_notation(self):
        # 大数下旧实现会得到 1.80144e+16 之类，新实现必须是完整十进制
        u = self.calc.bytes_to_units(2 ** 64 - 1)
        for unit, val in u.items():
            self.assertNotIn('e', val.lower(), "%s -> %r" % (unit, val))

    def test_full_decimal_value_matches(self):
        # 完整十进制必须与精确比值一致（用 Fraction 校验）
        from fractions import Fraction
        n = 3 * 1024 ** 3 + 7   # 3 GB + 7 字节，GB 为非整数
        u = self.calc.bytes_to_units(n)
        self.assertEqual(Fraction(u['GB']), Fraction(n, 1024 ** 3))


class TestBytesToUnitsHex(unittest.TestCase):
    def setUp(self):
        self.calc = CalcEngine()

    def test_integer_units_get_hex(self):
        h = self.calc.bytes_to_units_hex(4194304)   # 4 MB
        self.assertEqual(h['B'], '0x400000')
        self.assertEqual(h['KB'], '0x1000')
        self.assertEqual(h['MB'], '0x4')

    def test_non_integer_units_blank(self):
        h = self.calc.bytes_to_units_hex(4194304)   # 不是整数 GB/TB
        self.assertEqual(h['GB'], '')
        self.assertEqual(h['TB'], '')

    def test_zero_all_units(self):
        h = self.calc.bytes_to_units_hex(0)
        self.assertTrue(all(v == '0x0' for v in h.values()))


class TestExtractBits(unittest.TestCase):
    def setUp(self):
        self.calc = CalcEngine()

    def test_full_range(self):
        self.assertEqual(self.calc.extract_bits(0xABCD, 15, 0), 0xABCD)

    def test_byte_field(self):
        self.assertEqual(self.calc.extract_bits(0x12345678, 15, 8), 0x56)

    def test_single_bit(self):
        self.assertEqual(self.calc.extract_bits(0b1000, 3, 3), 1)
        self.assertEqual(self.calc.extract_bits(0b1000, 2, 2), 0)

    def test_top_bit(self):
        self.assertEqual(self.calc.extract_bits(1 << 63, 63, 63), 1)

    def test_reported_case_0x100_8_15(self):
        # 复现用户反馈：提取 0x100 的 bit8-15，应得到 1（无论高低位填写顺序）
        self.assertEqual(self.calc.extract_bits(0x100, 15, 8), 1)
        self.assertEqual(self.calc.extract_bits(0x100, 8, 15), 1)

    def test_order_independent(self):
        # 高低位写反应得到相同结果
        self.assertEqual(self.calc.extract_bits(0xFF, 3, 5),
                         self.calc.extract_bits(0xFF, 5, 3))

    def test_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            self.calc.extract_bits(0xFF, 64, 0)
        with self.assertRaises(ValueError):
            self.calc.extract_bits(0xFF, 5, -1)


class TestShift(unittest.TestCase):
    def setUp(self):
        self.calc = CalcEngine()

    def test_left_basic(self):
        self.assertEqual(self.calc.shift(1, 4, 'left'), 0x10)

    def test_right_basic(self):
        self.assertEqual(self.calc.shift(0x10, 4, 'right'), 1)

    def test_left_zero_count(self):
        self.assertEqual(self.calc.shift(0xABCD, 0, 'left'), 0xABCD)

    def test_left_overflow_masked(self):
        # 高位移出 64 位范围应被丢弃
        self.assertEqual(self.calc.shift(1 << 63, 1, 'left'), 0)
        self.assertEqual(self.calc.shift(self.calc.MAX_U64, 4, 'left'),
                         (self.calc.MAX_U64 << 4) & self.calc.MAX_U64)

    def test_right_logical(self):
        # 逻辑右移，高位补 0
        self.assertEqual(self.calc.shift(self.calc.MAX_U64, 60, 'right'), 0xF)

    def test_right_shift_out_all(self):
        self.assertEqual(self.calc.shift(self.calc.MAX_U64, 64, 'right'), 0)

    def test_negative_count_raises(self):
        with self.assertRaises(ValueError):
            self.calc.shift(1, -1, 'left')

    def test_count_too_large_raises(self):
        with self.assertRaises(ValueError):
            self.calc.shift(1, 65, 'left')

    def test_unknown_direction_raises(self):
        with self.assertRaises(ValueError):
            self.calc.shift(1, 1, 'up')


if __name__ == '__main__':
    unittest.main()
