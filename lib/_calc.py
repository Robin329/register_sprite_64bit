#!/usr/bin/python3
# RegisterSprite  Copyright (C) 2022-2023  Robin (jiangrenbin329@gmail.com)
#
# RegisterSprite is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
    @file: _calc.py
    @author: Robin
    @version: v1.0
    @date: 2026-05-20
    @brief: 安全算术表达式求值 + 字节单位换算（纯逻辑，不依赖 tkinter）
'''

import ast
import math
import operator


class CalcEngine():
    MAX_U64 = 2 ** 64 - 1
    UNITS = ['B', 'KB', 'MB', 'GB', 'TB']   # 第 idx 个单位 = 1024**idx 字节

    # 允许的二元运算符 -> 实现（禁用 ** 幂运算，避免巨数 DoS）
    _BIN_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
    }
    # 允许的一元运算符 -> 实现
    _UNARY_OPS = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def _eval_node(self, node):
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        if isinstance(node, ast.Constant):
            # 拒绝布尔/字符串/复数等，只允许 int/float
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError("非法表达式")
            return node.value
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._BIN_OPS:
                raise ValueError("不支持的运算符")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            try:
                return self._BIN_OPS[op_type](left, right)
            except ZeroDivisionError:
                raise ValueError("除数不能为零")
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._UNARY_OPS:
                raise ValueError("不支持的运算符")
            return self._UNARY_OPS[op_type](self._eval_node(node.operand))
        raise ValueError("非法表达式")

    def safe_eval(self, expr):
        '''对算术表达式做安全求值，返回 0~2^64-1 的整数，非法/越界抛 ValueError'''
        if expr is None or str(expr).strip() == "":
            raise ValueError("表达式为空")
        try:
            tree = ast.parse(str(expr), mode='eval')
        except SyntaxError:
            raise ValueError("表达式语法错误")
        value = self._eval_node(tree)
        if value < 0:                       # 在取整前判断，避免 (-1,0) 被截断为 0
            raise ValueError("结果不能为负")
        result = int(value)  # 最终向零截断取整
        if result > self.MAX_U64:
            raise ValueError("结果超出 64 位范围")
        return result

    def unit_to_bytes(self, value, unit):
        '''数值 + 单位 -> 字节数（向零截断），未知单位/无效数值/越界抛 ValueError'''
        if unit not in self.UNITS:
            raise ValueError("未知单位")
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError("无效数值")
        if not math.isfinite(value):   # 拒绝 inf/-inf/nan，统一为 ValueError
            raise ValueError("无效数值")
        idx = self.UNITS.index(unit)
        bytes_ = int(value * (1024 ** idx))
        if bytes_ < 0:
            raise ValueError("结果不能为负")
        if bytes_ > self.MAX_U64:
            raise ValueError("结果超出 64 位范围")
        return bytes_

    @staticmethod
    def _exact_decimal(n, idx):
        '''n / 1024**idx 的精确十进制字符串（永不使用科学计数，去除多余尾随 0）

        1024**idx == 2**(10*idx)，故 n / 2**k == (n * 5**k) / 10**k，
        分子为整数、分母为 10 的幂，可直接按位拼出精确十进制，避免浮点误差与科学计数。
        '''
        n = int(n)
        if idx == 0:
            return str(n)
        k = 10 * idx
        scaled = n * (5 ** k)            # 等于 n / 2**k 放大 10**k 倍后的整数
        s = str(scaled).rjust(k + 1, '0')
        int_part, frac_part = s[:-k], s[-k:]
        frac_part = frac_part.rstrip('0')
        return int_part if not frac_part else int_part + '.' + frac_part

    def bytes_to_units(self, n):
        '''字节数 -> {单位: 完整十进制字符串}，永不使用科学计数'''
        n = int(n)
        return {unit: self._exact_decimal(n, idx)
                for idx, unit in enumerate(self.UNITS)}

    def bytes_to_units_hex(self, n):
        '''字节数 -> {单位: 十六进制字符串}，仅当该单位换算结果为整数时给出，否则为空串'''
        n = int(n)
        result = {}
        for idx, unit in enumerate(self.UNITS):
            divisor = 1024 ** idx
            result[unit] = hex(n // divisor) if n % divisor == 0 else ''
        return result

    def extract_bits(self, value, high, low):
        '''从 64 位 value 中提取 [high:low] 位字段（含两端），返回整数。

        高低位可任意顺序填写（自动归一），但两个位号都必须在 0~63 之间，否则抛 ValueError。
        '''
        value = int(value) & self.MAX_U64
        high = int(high)
        low = int(low)
        if high < low:                      # 容忍“高低位写反”，例如把 bit8-15 填成 高8 低15
            high, low = low, high
        if not (0 <= low <= high <= 63):
            raise ValueError("位号必须在 0~63 之间")
        width = high - low + 1
        mask = (1 << width) - 1
        return (value >> low) & mask


def main():
    calc = CalcEngine()
    print(calc.safe_eval("(10+100)*20*(50/10)"))    # 11000
    print(calc.unit_to_bytes(4, 'MB'))              # 4194304
    print(calc.bytes_to_units(4194304))             # {'B': '4194304', 'MB': '4', ...}
    print(calc.bytes_to_units_hex(4194304))         # {'B': '0x400000', 'GB': '', ...}
    print(calc.extract_bits(0x12345678, 15, 8))     # 0x56 -> 86


if __name__ == '__main__':
    main()
