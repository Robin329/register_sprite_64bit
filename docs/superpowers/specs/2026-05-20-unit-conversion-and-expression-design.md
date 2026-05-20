# 单位换算 + 10 进制表达式求值 — 设计文档

- 日期：2026-05-20
- 项目：Register Sprite 64bit（寄存器小精灵，Python + tkinter）
- 作者：Robin329 / 协作：Claude

## 1. 背景与现状

`main.py` 是单文件 `MyGui(Frame)` 应用（1300+ 行），把 64 位寄存器以 64 个位按钮可视化，并在底部做 16/10/8/2 进制互转。`lib/` 下每个模块一个类、带 GPL 头与 `@file/@author/...` 文档串、自带 `main()` 自测（见 `_file_operations.py`、`_color_operations.py`）。

现状中与本次需求相关的两处：

- **数据大小显示**（`show_data()` 约 925–950 行）：把寄存器 10 进制值按阈值“自动选一个单位”（bits/Byte/KByte/MByte/GByte/TByte）只读显示，且把值当作 **bit 数** 处理（`/8` 得字节）。只能看，不能反向换算。
- **10 进制框 + 计算器**：`update_dec_btn_val_by_entry` 已经调用 `eval()`，但与 `calc_add/calc_sub/calc_multi/calc_div/calc_equal` 标志位状态机纠缠，逻辑混乱；`eval` 不安全；结果未做 64 位边界处理。`+ - * / =` 按钮通过设置上述标志位驱动两个回车 handler。

## 2. 目标

1. **单位换算（基数 1024）**：
   - 新增“输入值 + 单位下拉（B/KB/MB/GB/TB）”的反向换算输入：输入数值并选单位 → 算出字节数 → 写入寄存器位 → 同步刷新 10/16/8/2 进制框。
   - 新增**只读多单位显示**：同时显示当前寄存器值的 B/KB/MB/GB/TB 五个值，随寄存器变化实时刷新。
   - 语义：**寄存器 10 进制值 = 字节数（Byte）**。例：输入 `4 MB` → `4194304` 字节 → 写入寄存器；`4194304` → B=4194304 / KB=4096 / MB=4。
   - 进制基数：`1KB=1024B`，`1MB=1024KB`，依此类推。

2. **10 进制框支持完整算术表达式**：
   - 例：`(10+100)*20*(50/10)` = `11000`。
   - 运算规则：标准数学优先级；`/` 为真除（`50/10=5.0`）；**最终结果 `int()` 取整**（`7/2 → 3`）。
   - 范围校验：结果须满足 `0 ≤ 结果 ≤ 2^64-1`；越界、负结果、非法表达式 → 弹窗报错，寄存器与显示保持不变。

3. **移除 `+ - * / =` 按钮**及其标志位状态机（与新表达式输入功能重叠/冲突）。

## 3. 非目标（YAGNI）

- 不为 16 进制 / 8 进制框增加表达式求值（仅 10 进制框）。
- 表达式**不支持位运算符与幂运算**（`& | ^ << >> **`）：位操作已有专门的“左移/右移/求非”按钮；禁用 `**` 同时规避 `2**10**10` 这类拒绝服务式巨数。
- 不改寄存器位按钮布局、颜色/菜单/配置等既有功能。

## 4. 架构

```
lib/_calc.py   ← 新增。纯逻辑：安全表达式求值 + 单位换算（不依赖 tkinter，可单测）
main.py        ← UI 接线 + 抽取 set_register_bits() 复用，删除旧计算器状态机
tests/test_calc.py ← 新增。CalcEngine 单元测试
```

设计要点：两个新功能本质都是“输入 → 得到一个整数 → 写入 64 位寄存器 → 刷新所有显示”，因此把“整数 → 设置位按钮”的逻辑抽成一个共用方法，纯计算逻辑下沉到可测试模块。

## 5. `lib/_calc.py` — `CalcEngine`（纯逻辑）

沿用 `lib/` 类风格（GPL 头 + 文档串 + `main()` 自测）。

```python
class CalcEngine:
    MAX_U64 = 2**64 - 1
    UNITS = ['B', 'KB', 'MB', 'GB', 'TB']   # 第 idx 个单位 = 1024**idx 字节

    def safe_eval(self, expr: str) -> int: ...
    def unit_to_bytes(self, value: float, unit: str) -> int: ...
    def bytes_to_units(self, n: int) -> dict: ...   # {'B':str, 'KB':str, ...} 已格式化
```

### 5.1 `safe_eval(expr) -> int`
- 用 `ast.parse(expr, mode='eval')` 解析；递归遍历，**仅允许**以下节点：
  - `Expression`、`Constant`（仅 int/float）
  - `BinOp`，运算符限 `Add, Sub, Mult, Div, FloorDiv, Mod`
  - `UnaryOp`，运算符限 `UAdd, USub`
  - 括号天然由 AST 结构表达，无需特判
- 其它节点（`Name`、`Call`、`Attribute`、`Subscript`、`BitXor`、`Pow` 等）→ 抛 `ValueError("非法表达式")`。
- 求值后 `result = int(value)`（向零截断取整）。
- 范围校验：`0 ≤ result ≤ MAX_U64`，否则抛 `ValueError`（消息含中文，如“结果超出 64 位范围”/“结果不能为负”）。
- 空串/语法错误 → 抛 `ValueError`（消息友好）。
- 除零等运算异常 → 捕获并转抛 `ValueError`。

### 5.2 `unit_to_bytes(value, unit) -> int`
- `idx = UNITS.index(unit)`（unit 不在表内 → `ValueError`）。
- `bytes_ = int(value * (1024 ** idx))`（向零截断）。
- 范围校验 `0 ≤ bytes_ ≤ MAX_U64`，否则 `ValueError`。

### 5.3 `bytes_to_units(n) -> dict`
- 返回 `{'B': ..., 'KB': ..., 'MB': ..., 'GB': ..., 'TB': ...}`。
- `B` 显示为整数字符串；`KB/MB/GB/TB` 为 `n / 1024**idx` 的格式化字符串（用如 `f"{v:.6g}"`，避免过长尾数）。
- 由 UI 直接填入只读输入框。

## 6. `main.py` 改动

### 6.1 删除（旧计算器状态机）
- 类变量：`expression, calc_add, calc_sub, calc_multi, calc_div, calc_equal, expres`。
- 方法：`calc_add, calc_sub, calc_multi, calc_div, calc_equal, evaluate_expression, clear_expression`。
- `init_view()` 中 `+ - * / =` 五个按钮的创建代码（约 717–752 行）及其 `calc_btn_frame`。
- `show_data()` 中引用 `self.calc_equal / self.expression` 的分支（约 839–842 行）。
- **全局清查**：搜索所有 `calc_` / `expression` / `expres` 引用，确保无遗留（否则 `AttributeError`）。

### 6.2 新增 / 重写
- `__init__`：`self.calc = _calc.CalcEngine()`（注意：与被删除的 `calc_*` 方法不再冲突）。
- **新增 `set_register_bits(self, value: int)`**：`value → bin(value)[2:] → 左侧补 0 至 64 位（多余高位截断）→ 遍历 `self.btn_list` 设 `text` → `self.update_btn_style()`。供 16/10 进制框与单位换算共用。
- **重写 `update_dec_btn_val_by_entry(self, event)`**（10 进制框回车）：
  ```
  try:
      value = self.calc.safe_eval(self.decimal_output.get())
      self.set_register_bits(value)
      self.show_data()
  except ValueError as e:
      messagebox.showerror("错误", str(e))
  ```
- **重写 `update_btn_val_by_entry(self, event)`**（16 进制框回车）：去掉 `calc_*` 分支；剥离可选 `0x` 前缀；用 `int(text, 16)` 解析（非法 → 弹窗报错）→ `set_register_bits` → `show_data`。
- **`show_data()`**：`dec = int(_bin, 2)` 即字节数；删除单位单选逻辑（925–950），改为 `units = self.calc.bytes_to_units(dec)` 后刷新 5 个只读单位框。
- `init_view()`：
  - 删除 `+ - * / =` 按钮区。
  - 新增**单位换算输入行**：`Label("单位换算") + Entry(self.entry_unit_value) + OptionMenu(self.unit_var, *CalcEngine.UNITS)`；`entry_unit_value` 绑 `<Return>`、`unit_var` 绑 `trace`/command → `self.convert_unit_to_register`。
  - 把 `frame_data_size` 区改为**多单位只读显示**：5 个 `Label + 只读 Entry`（`state='readonly'`），分别对应 B/KB/MB/GB/TB，存入 `self.size_entries` 字典便于刷新。
- **新增 `convert_unit_to_register(self, event=None)`**：
  ```
  try:
      bytes_ = self.calc.unit_to_bytes(float(self.entry_unit_value.get()), self.unit_var.get())
      self.set_register_bits(bytes_)
      self.show_data()
  except ValueError:
      messagebox.showerror("错误", "无效的单位换算输入")
  ```
- `init_value()` / `clear_value()`：移除对已删控件（`entry_bin_size` 等）的引用；新增对单位换算输入框与多单位只读框的初始化/清空。
- `ChangeBackgroundColor()`：更新背景色设置中对控件的引用——移除已删控件、加入新控件，避免 `AttributeError`。

## 7. UI 布局

- 单位换算输入行与多单位只读显示均置于现有 `frame_choice` 区（沿用原 `frame_data_size` 的位置风格），不影响上方寄存器位按钮与四进制框。
- 多单位用只读 `Entry` 而非 `Label`，方便用户复制数值。

```
┌ 单位换算 ───────────────────────┐
│ 数值 [ 4        ]  单位 [ MB ▼ ] │  ← 回车/切换单位即换算
└─────────────────────────────────┘
┌ 当前值各单位（只读） ───────────┐
│ B  [ 4194304 ]   KB [ 4096 ]    │
│ MB [ 4 ]  GB [ 0.003906 ] TB[…] │
└─────────────────────────────────┘
```

## 8. 错误处理

- `CalcEngine` 一律以 `ValueError`（中文消息）表达失败。
- UI 层捕获后 `messagebox.showerror("错误", str(e))`，**不改动寄存器与各显示框**。

## 9. 测试

### 9.1 `tests/test_calc.py`（纯逻辑，无需 GUI）
- `safe_eval`：
  - `(10+100)*20*(50/10) == 11000`
  - `7/2 == 3`（截断）、`(2+3)*4 == 20`、嵌套括号、`100-1 == 99`
  - 中间出现负数但最终非负：如 `(5-3)*10 == 20`
  - 边界：`0`、`2**64-1`（写成字面量 `18446744073709551615`）合法
  - 越界：`18446744073709551616` → `ValueError`
  - 负结果：`5-10` → `ValueError`
  - 非法：`"abc"`、`"__import__('os')"`、`"a+1"`、`"2**8"`（禁幂）、`"len([])"`、空串 `""` → 均 `ValueError`
  - 除零：`"1/0"` → `ValueError`
- `unit_to_bytes`：`(4,'MB')==4194304`、`(1,'KB')==1024`、`(0,'B')==0`、`(0.5,'KB')==512`、越界 → `ValueError`、未知单位 → `ValueError`。
- `bytes_to_units`：`4194304 → B='4194304', KB='4096', MB='4'`（数值正确，格式可接受）。

### 9.2 GUI 手动验证
- 起应用：10 进制框输入 `(10+100)*20*(50/10)` 回车 → 显示 11000，位按钮/各进制同步。
- 单位换算输入 `4` 选 `MB` 回车 → 寄存器变 4194304，多单位框显示 B/KB/MB/GB/TB。
- 非法表达式 / 越界 / 非法单位输入 → 弹窗报错且界面不变。
- 切换背景色不报错（验证控件引用清理无遗漏）。

## 10. 风险

- **主要风险**：删除旧计算器后若残留对 `calc_* / expression / expres` 或已删控件的引用 → 运行期 `AttributeError`。实施时必须全局搜索这些标识符确认清零，并实际启动应用走查每个功能（含背景色切换）。
