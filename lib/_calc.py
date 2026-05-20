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
import operator


class CalcEngine():
    MAX_U64 = 2 ** 64 - 1

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
        result = int(value)  # 最终向零截断取整
        if result < 0:
            raise ValueError("结果不能为负")
        if result > self.MAX_U64:
            raise ValueError("结果超出 64 位范围")
        return result


def main():
    calc = CalcEngine()
    print(calc.safe_eval("(10+100)*20*(50/10)"))   # 11000


if __name__ == '__main__':
    main()
