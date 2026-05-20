# 单位换算 + 10 进制表达式求值 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Register Sprite 64bit 增加 1024 基数的字节单位换算（输入值+单位写入寄存器、只读多单位显示）以及 10 进制框的安全算术表达式求值，并移除旧的 `+ - * / =` 计算器状态机。

**Architecture:** 纯逻辑（安全表达式求值、单位换算）下沉到新模块 `lib/_calc.py`，可用 `unittest` 单测；`main.py` 仅做 UI 接线，并抽取共用的 `set_register_bits()` 把整数写入 64 位按钮。

**Tech Stack:** Python 3.10、tkinter（标准库 `from tkinter import *`）、`ast`/`operator`（安全求值）、`unittest`（测试，pytest 未安装）。

**约定：所有命令在仓库根目录 `F:/Linux/register_sprite_64bit` 下执行。**

---

### Task 1: `CalcEngine.safe_eval` — 安全表达式求值

**Files:**
- Create: `lib/_calc.py`
- Test: `tests/test_calc.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/test_calc.py`：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python tests/test_calc.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib._calc'`

- [ ] **Step 3: 实现 `lib/_calc.py`（仅 `safe_eval`）**

```python
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python tests/test_calc.py -v`
Expected: PASS（13 个 `TestSafeEval` 用例全部 ok）

- [ ] **Step 5: 提交**

```bash
git add lib/_calc.py tests/test_calc.py
git commit -m "feat(calc): add safe arithmetic expression evaluator"
```

---

### Task 2: `CalcEngine.unit_to_bytes` — 单位转字节（1024 基数）

**Files:**
- Modify: `lib/_calc.py`
- Test: `tests/test_calc.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_calc.py` 中，`TestSafeEval` 类之后、`if __name__` 之前插入：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python tests/test_calc.py -v`
Expected: FAIL — `AttributeError: 'CalcEngine' object has no attribute 'unit_to_bytes'`

- [ ] **Step 3: 实现 `unit_to_bytes`**

在 `lib/_calc.py` 中，把 `MAX_U64` 那一行替换为新增 `UNITS` 列表：

找到：
```python
    MAX_U64 = 2 ** 64 - 1
```
替换为：
```python
    MAX_U64 = 2 ** 64 - 1
    UNITS = ['B', 'KB', 'MB', 'GB', 'TB']   # 第 idx 个单位 = 1024**idx 字节
```

在 `safe_eval` 方法之后新增方法：
```python
    def unit_to_bytes(self, value, unit):
        '''数值 + 单位 -> 字节数（向零截断），未知单位/无效数值/越界抛 ValueError'''
        if unit not in self.UNITS:
            raise ValueError("未知单位")
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise ValueError("无效数值")
        idx = self.UNITS.index(unit)
        bytes_ = int(value * (1024 ** idx))
        if bytes_ < 0:
            raise ValueError("结果不能为负")
        if bytes_ > self.MAX_U64:
            raise ValueError("结果超出 64 位范围")
        return bytes_
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python tests/test_calc.py -v`
Expected: PASS（`TestSafeEval` + `TestUnitToBytes` 全部 ok）

- [ ] **Step 5: 提交**

```bash
git add lib/_calc.py tests/test_calc.py
git commit -m "feat(calc): add unit_to_bytes conversion (base 1024)"
```

---

### Task 3: `CalcEngine.bytes_to_units` — 字节转各单位

**Files:**
- Modify: `lib/_calc.py`
- Test: `tests/test_calc.py`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_calc.py` 中，`TestUnitToBytes` 类之后、`if __name__` 之前插入：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python tests/test_calc.py -v`
Expected: FAIL — `AttributeError: 'CalcEngine' object has no attribute 'bytes_to_units'`

- [ ] **Step 3: 实现 `bytes_to_units`**

在 `lib/_calc.py` 的 `unit_to_bytes` 之后新增方法：
```python
    def bytes_to_units(self, n):
        '''字节数 -> {单位: 已格式化字符串}，B 为整数，其余保留有效数字'''
        n = int(n)
        result = {}
        for idx, unit in enumerate(self.UNITS):
            if idx == 0:
                result[unit] = str(n)
            else:
                result[unit] = "{:.6g}".format(n / (1024 ** idx))
        return result
```

并更新 `main()` 自测（可选），把它替换为：
```python
def main():
    calc = CalcEngine()
    print(calc.safe_eval("(10+100)*20*(50/10)"))   # 11000
    print(calc.unit_to_bytes(4, 'MB'))              # 4194304
    print(calc.bytes_to_units(4194304))             # {'B': '4194304', ...}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python tests/test_calc.py -v`
Expected: PASS（三个测试类全部 ok）

- [ ] **Step 5: 提交**

```bash
git add lib/_calc.py tests/test_calc.py
git commit -m "feat(calc): add bytes_to_units multi-unit formatting"
```

---

### Task 4: main.py 后端接线 + 移除旧计算器状态机

> 本任务完成后，应用仍可运行：10 进制框变为表达式求值，旧的"自动单选单位"显示暂时保留（Task 5 再替换）。`+ - * / =` 按钮被移除。

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 引入 `_calc` 模块**

找到：
```python
from lib import _file_operations
from lib import _debug
from lib import _color_operations
```
替换为：
```python
from lib import _file_operations
from lib import _debug
from lib import _color_operations
from lib import _calc
```

- [ ] **Step 2: 删除类级状态变量**

找到并删除整段：
```python
    # 类里面定义全局变量
    expression = 0
    calc_add = 0
    calc_sub = 0
    calc_multi = 0
    calc_div = 0
    calc_equal = 0
    expres = ""
```

- [ ] **Step 3: 在 `__init__` 实例化引擎**

找到：
```python
        self.fops = _file_operations.FileOperations()  # 配置文件操作
        self.fontstyle = _color_operations.FontStyle()  # 终端打印样式
```
替换为：
```python
        self.fops = _file_operations.FileOperations()  # 配置文件操作
        self.fontstyle = _color_operations.FontStyle()  # 终端打印样式
        self.calc = _calc.CalcEngine()  # 计算/单位换算引擎
```

- [ ] **Step 4: 重写两个 Entry 回车 handler 并新增 `set_register_bits`/`convert_unit_to_register`**

把从 `# event start` 到 `# event end` 之间的全部内容（两个旧方法 `update_dec_btn_val_by_entry`、`update_btn_val_by_entry`）整体替换。

找到从这一行开始：
```python
    # event start ***************************************************
    # 10进制Entry回车事件处理函数
    def update_dec_btn_val_by_entry(self, event):
```
到这一行结束（含）：
```python
    # event end ***************************************************
```
整段替换为：
```python
    # event start ***************************************************
    # 将一个整数写入 64 个位按钮（高位在前，btn_list[0] 为 bit63）
    def set_register_bits(self, value):
        value = int(value) & ((1 << 64) - 1)
        str_bin_data = format(value, '064b')
        for idx, btn in enumerate(self.btn_list):
            btn['text'] = str_bin_data[idx]
        self.update_btn_style()

    # 10进制Entry回车事件处理函数：对输入做安全表达式求值
    def update_dec_btn_val_by_entry(self, event):
        try:
            value = self.calc.safe_eval(self.decimal_output.get())
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
        self.set_register_bits(value)
        self.show_data()

    # 单位换算输入处理：数值 + 单位 -> 字节数 -> 写入寄存器
    def convert_unit_to_register(self, event=None):
        try:
            bytes_ = self.calc.unit_to_bytes(
                self.entry_unit_value.get(), self.unit_var.get())
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
        self.set_register_bits(bytes_)
        self.show_data()

    # 16进制Entry回车事件处理函数
    def update_btn_val_by_entry(self, event):
        origin_data = self.hex_output.get().strip()
        if origin_data[0:2].lower() == "0x":
            origin_data = origin_data[2:]
        try:
            value = int(origin_data, 16)
            if value < 0 or value > self.calc.MAX_U64:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "无效的 16 进制输入")
            return
        self.set_register_bits(value)
        self.show_data()

    # event end ***************************************************
```

- [ ] **Step 5: 删除 `show_data` 中的 `calc_equal` 分支**

找到：
```python
        dec = int(_bin, 2)
        if self.calc_equal == 1:
            dec = self.expression
            print("dec: %d" % dec)
            print(f"dec: {dec}")
        not_dec = int(not_bin, 2)
```
替换为：
```python
        dec = int(_bin, 2)
        not_dec = int(not_bin, 2)
```

- [ ] **Step 6: 删除 `+ - * / =` 按钮创建代码**

在 `init_view` 中找到并删除整段（从 `# "+"` 注释到 `=` 按钮 pack 为止）：
```python
        # "+"
        self.calc_btn_frame = Frame(self.frame_choice)
        self.add_btn = Button(self.calc_btn_frame,
                              background=self.btn_color.value,
                              text="+", width=3, height=1)
        self.add_btn.config(command=self.calc_add)
        self.add_btn.pack(side=LEFT)
        self.calc_btn_frame.pack(side=TOP)

        # "-"
        self.sub_btn = Button(self.calc_btn_frame,
                              background=self.btn_color.value,
                              text="-", width=3, height=1)
        self.sub_btn.config(command=self.calc_sub)
        self.sub_btn.pack(side=LEFT)

        # "*"
        self.multi_btn = Button(self.calc_btn_frame,
                                background=self.btn_color.value,
                                text="*", width=3, height=1)
        self.multi_btn.config(command=self.calc_multi)
        self.multi_btn.pack(side=LEFT)

        # "/"
        self.div_btn = Button(self.calc_btn_frame,
                              background=self.btn_color.value,
                              text="/", width=3, height=1)
        self.div_btn.config(command=self.calc_div)
        self.div_btn.pack(side=LEFT)

        # "="
        self.div_btn = Button(self.calc_btn_frame,
                              background=self.btn_color.value,
                              text="=", width=3, height=1)
        self.div_btn.config(command=self.calc_equal)
        self.div_btn.pack(side=LEFT)

```

- [ ] **Step 7: 删除旧计算器方法**

删除从 `evaluate_expression` 到 `calc_equal` 的整段（含其前置注释），即从这一行：
```python
    # 计算表达式的函数
    def evaluate_expression(self):
        self.expres = self.decimal_output.get()
```
一直到 `calc_equal` 方法结尾这一行（含）：
```python
        self.calc_equal = 0
```
中间包含 `evaluate_expression`、`clear_expression`、`calc_add`、`calc_sub`、`calc_multi`、`calc_div`、`calc_equal` 七个方法及它们之间的 `'''计算器X功能函数'''` 注释块，全部删除。

**保留**紧随其后的求非注释与方法（不要删）：
```python
    '''
        求非功能函数
    '''

    @_debug.printk()
    def calc_not(self):
```

- [ ] **Step 8: 静态导入检查 + 单测仍通过**

Run: `python -c "import main"`
Expected: 仅打印 `---lib imported---` 之类，无 Traceback（确认无语法错误/类定义期 NameError）。

Run: `python tests/test_calc.py -v`
Expected: PASS（不受影响）。

- [ ] **Step 9: 全局排查残留引用**

Run（应**无输出**，即不再有任何引用）：
```bash
git grep -nE "calc_add|calc_sub|calc_multi|calc_div|calc_equal|evaluate_expression|clear_expression|self\.expression|self\.expres\b" -- main.py
```
Expected: 空输出。若有命中，按上下文删除/修正后再继续。

- [ ] **Step 10: 提交**

```bash
git add main.py
git commit -m "refactor(main): expression-eval decimal entry, drop +-*/= state machine"
```

---

### Task 5: main.py UI — 单位换算输入 + 只读多单位显示

> 替换旧的"自动单选单位"显示为：单位换算输入行（数值 + 下拉）+ 五个只读单位框，并把刷新接到 `show_data`。

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 替换 `frame_data_size` 区为单位换算输入 + 多单位显示**

在 `init_view` 中找到整段：
```python
        # 数据大小，单位KB
        self.frame_data_size = Frame(self.frame_choice)
        self.label_bin_size = Label(self.frame_data_size,
                                    background=self.bg_color.value,
                                    text="数据大小",
                                    font=("宋体", 9, "bold"))
        self.label_bin_size.pack(side=LEFT)
        self.entry_bin_size = Entry(self.frame_data_size,
                                    background='#f0f0f0',
                                    width=10,
                                    font=("宋体", 12, "bold"))

        self.entry_bin_size.pack(side=LEFT)
        self.label_unit_size = Label(self.frame_data_size,
                                     background=self.bg_color.value,
                                     text="bits",
                                     font=("宋体", 9, "bold"))
        self.label_unit_size.pack(side=LEFT)
        self.frame_data_size.configure(bg=self.bg_color.value)
        self.frame_data_size.pack(side=TOP, pady=5, anchor='e')
```
替换为：
```python
        # 单位换算输入区：输入数值 + 选择单位 -> 写入寄存器
        self.frame_unit_input = Frame(self.frame_choice)
        self.label_unit_input = Label(self.frame_unit_input,
                                      background=self.bg_color.value,
                                      text="单位换算",
                                      font=("宋体", 9, "bold"))
        self.label_unit_input.pack(side=LEFT)
        self.entry_unit_value = Entry(self.frame_unit_input,
                                      background='#f0f0f0',
                                      width=12,
                                      font=("宋体", 12, "bold"))
        self.entry_unit_value.bind('<Return>', func=self.convert_unit_to_register)
        self.entry_unit_value.pack(side=LEFT)
        self.unit_var = StringVar()
        self.unit_var.set(_calc.CalcEngine.UNITS[0])
        self.option_unit = OptionMenu(self.frame_unit_input, self.unit_var,
                                      *_calc.CalcEngine.UNITS,
                                      command=self.convert_unit_to_register)
        self.option_unit.config(background=self.btn_color.value)
        self.option_unit.pack(side=LEFT)
        self.frame_unit_input.configure(bg=self.bg_color.value)
        self.frame_unit_input.pack(side=TOP, pady=5)

        # 多单位只读显示区：展示当前寄存器值（字节数）对应的各单位
        self.frame_data_size = Frame(self.frame_choice)
        self.size_entries = {}
        for unit in _calc.CalcEngine.UNITS:
            row = Frame(self.frame_data_size)
            lbl = Label(row, background=self.bg_color.value,
                        text=unit, width=4, anchor='e',
                        font=("宋体", 9, "bold"))
            lbl.pack(side=LEFT)
            ent = Entry(row, background='#f0f0f0', width=22,
                        font=("宋体", 11, "bold"))
            ent.pack(side=LEFT)
            ent.insert(0, '0')
            ent['state'] = 'readonly'
            row.configure(bg=self.bg_color.value)
            row.pack(side=TOP, anchor='e')
            self.size_entries[unit] = ent
        self.frame_data_size.configure(bg=self.bg_color.value)
        self.frame_data_size.pack(side=TOP, pady=5, anchor='e')
```

- [ ] **Step 2: 把 `show_data` 的旧单位逻辑替换为多单位刷新**

找到整段：
```python
        # 这里要注意，如果将十进制数据进行大小计算，需要在原数据上+1
        this_dec = dec
        result = 0
        # 一些单位换算，后期可以独立出来作为功能甘薯
        if this_dec < 8:
            result = this_dec
            self.label_unit_size['text'] = "bits"
        elif this_dec >= 8 and this_dec < 1024:
            result = this_dec / 8
            self.label_unit_size['text'] = "Byte"
        elif this_dec >= 1024 and this_dec < 0x100000:
            result = this_dec / 1024
            self.label_unit_size['text'] = "KByte"
        elif this_dec >= 0x100000 and this_dec < 0x40000000:
            result = this_dec / 0x100000
            self.label_unit_size['text'] = "MByte"
        elif this_dec >= 0x40000000 and this_dec < 0x10000000000:
            this_dec = dec + 1
            result = this_dec / 0x40000000
            self.label_unit_size['text'] = "GByte"
        else:
            this_dec = dec + 1
            result = this_dec / 0x10000000000
            self.label_unit_size['text'] = "TByte"

        self.entry_bin_size.insert(0, result)
        self.binary_output['state'] = 'readonly'  # 将二进制回显区设置为只读
```
替换为：
```python
        # 数据大小：寄存器值视为字节数，同时显示各单位（只读）
        units = self.calc.bytes_to_units(dec)
        for unit, entry in self.size_entries.items():
            entry['state'] = 'normal'
            entry.delete(0, END)
            entry.insert(0, units[unit])
            entry['state'] = 'readonly'
        self.binary_output['state'] = 'readonly'  # 将二进制回显区设置为只读
```

- [ ] **Step 3: 更新 `clear_value` 对已删控件的引用**

找到：
```python
        self.entry_hex_shift_set.delete(0, END)
        self.entry_hex_shift_clear.delete(0, END)
        self.entry_bin_size.delete(0, END)
        self.binary_output['state'] = 'readonly'
```
替换为：
```python
        self.entry_hex_shift_set.delete(0, END)
        self.entry_hex_shift_clear.delete(0, END)
        for ent in self.size_entries.values():
            ent['state'] = 'normal'
            ent.delete(0, END)
            ent['state'] = 'readonly'
        self.binary_output['state'] = 'readonly'
```

- [ ] **Step 4: 更新 `ChangeBackgroundColor` 对已删控件的引用**

找到：
```python
            # 数据大小背景色更换
            self.frame_data_size.config(bg=self.bg_color.value)
            self.label_bin_size.config(bg=self.bg_color.value)
            self.label_unit_size.config(bg=self.bg_color.value)
```
替换为：
```python
            # 数据大小/单位换算背景色更换
            self.frame_unit_input.config(bg=self.bg_color.value)
            self.label_unit_input.config(bg=self.bg_color.value)
            self.frame_data_size.config(bg=self.bg_color.value)
            for unit_row in self.frame_data_size.winfo_children():
                unit_row.config(bg=self.bg_color.value)
                for child in unit_row.winfo_children():
                    if isinstance(child, Label):
                        child.config(bg=self.bg_color.value)
```

- [ ] **Step 5: 静态导入检查 + 残留引用排查**

Run: `python -c "import main"`
Expected: 无 Traceback。

Run（应无输出）：
```bash
git grep -nE "entry_bin_size|label_bin_size|label_unit_size" -- main.py
```
Expected: 空输出。

- [ ] **Step 6: 提交**

```bash
git add main.py
git commit -m "feat(main): unit conversion input + read-only multi-unit display"
```

---

### Task 6: 端到端冒烟测试 + 手动验收

**Files:**
- Create: `tests/smoke_gui.py`

- [ ] **Step 1: 创建冒烟脚本**

创建 `tests/smoke_gui.py`（需要桌面会话，验证无残留引用并打通表达式/换算两条链路）：

```python
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from main import MyGui


def main():
    root = tk.Tk()
    app = MyGui(master=root)

    # 1) 表达式求值
    app.decimal_output.delete(0, tk.END)
    app.decimal_output.insert(0, "(10+100)*20*(50/10)")
    app.update_dec_btn_val_by_entry(None)
    assert app.decimal_output.get() == "11000", \
        "expr eval failed: %r" % app.decimal_output.get()

    # 2) 单位换算 4 MB -> 4194304 字节，并校验多单位显示
    app.entry_unit_value.delete(0, tk.END)
    app.entry_unit_value.insert(0, "4")
    app.unit_var.set("MB")
    app.convert_unit_to_register()
    assert app.decimal_output.get() == "4194304", \
        "unit convert failed: %r" % app.decimal_output.get()
    assert app.size_entries["MB"].get() == "4", \
        "MB display failed: %r" % app.size_entries["MB"].get()
    assert app.size_entries["KB"].get() == "4096", \
        "KB display failed: %r" % app.size_entries["KB"].get()

    # 3) 复位与背景色切换不应抛异常（验证无残留控件引用）
    app.bit_reset()
    app.ChangeBackgroundColor("纯白")

    print("SMOKE OK")
    root.destroy()


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 运行冒烟脚本**

Run: `python tests/smoke_gui.py`
Expected: 打印 `SMOKE OK`，无 AssertionError / Traceback。

- [ ] **Step 3: 手动验收（启动真实界面）**

Run: `python main.py`
逐项确认：
1. 10 进制框输入 `(10+100)*20*(50/10)` 回车 → 各进制显示 11000，位按钮同步点亮。
2. 单位换算框输入 `4`、单位选 `MB` 回车（或切换单位）→ 10 进制变 `4194304`，多单位区显示 `B=4194304 / KB=4096 / MB=4 / GB≈0.00390625 / TB≈...`。
3. 10 进制框输入非法表达式（如 `a+1`）、越界（如 `5-10`）→ 弹窗报错，界面数据不变。
4. 16 进制框输入 `0x400000` 回车 → 10 进制变 4194304。
5. 菜单"文件→设置→背景色"选色应用 → 界面整体换色，无报错（验证新控件背景色已接好）。
6. 左移/右移/求非/复位按钮工作正常。

- [ ] **Step 4: 提交**

```bash
git add tests/smoke_gui.py
git commit -m "test: add end-to-end gui smoke test for calc and unit conversion"
```

---

## 自查（Self-Review）

**规格覆盖：**
- 单位换算输入（值+单位下拉，1024 基数，写寄存器并同步各进制）→ Task 5 Step 1 + Task 4（`convert_unit_to_register`）+ Task 2。✔
- 只读多单位同时显示 → Task 5 Step 1/Step 2 + Task 3。✔
- 寄存器值=字节数语义 → Task 5 Step 2（`bytes_to_units(dec)`）。✔
- 10 进制表达式求值（真除、最终取整、0~2^64-1 校验、报错）→ Task 1 + Task 4 Step 4。✔
- 禁位运算/幂运算 → Task 1（`_BIN_OPS` 不含 Pow/位运算）+ `test_pow_rejected`。✔
- 移除 `+ - * / =` 按钮及状态机 → Task 4 Step 2/6/7 + Step 9 残留排查。✔
- 错误用 `messagebox.showerror` 且不改界面 → Task 4 Step 4、Task 4（convert）。✔
- 风险：残留引用 → Task 4 Step 9 / Task 5 Step 5 grep + Task 6 冒烟。✔

**占位符扫描：** 无 TBD/TODO；所有代码步骤含完整代码。✔

**类型/命名一致性：** `CalcEngine.safe_eval / unit_to_bytes / bytes_to_units / MAX_U64 / UNITS`、`set_register_bits / convert_unit_to_register / entry_unit_value / unit_var / size_entries / frame_unit_input / label_unit_input` 在各任务间一致。✔
