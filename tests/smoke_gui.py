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

    # 2) 在 MB 框直接输入 4 + 回车 -> 4194304 字节，并校验各单位框刷新
    app.size_entries["MB"].delete(0, tk.END)
    app.size_entries["MB"].insert(0, "4")
    app.convert_size_entry("MB")
    assert app.decimal_output.get() == "4194304", \
        "unit convert failed: %r" % app.decimal_output.get()
    assert app.size_entries["MB"].get() == "4", \
        "MB display failed: %r" % app.size_entries["MB"].get()
    assert app.size_entries["KB"].get() == "4096", \
        "KB display failed: %r" % app.size_entries["KB"].get()

    # 2b) 在 KB 框输入 2048 + 回车 -> 2097152 字节，MB 应显示 2
    app.size_entries["KB"].delete(0, tk.END)
    app.size_entries["KB"].insert(0, "2048")
    app.convert_size_entry("KB")
    assert app.decimal_output.get() == "2097152", \
        "KB input failed: %r" % app.decimal_output.get()
    assert app.size_entries["MB"].get() == "2", \
        "MB after KB input failed: %r" % app.size_entries["MB"].get()

    # 3) 十六进制栏：整数单位显示 hex，非整数单位留空（4 MB = 4194304 字节）
    app.size_entries["MB"].delete(0, tk.END)
    app.size_entries["MB"].insert(0, "4")
    app.convert_size_entry("MB")
    assert app.size_hex_entries["B"].get() == "0x400000", \
        "B hex failed: %r" % app.size_hex_entries["B"].get()
    assert app.size_hex_entries["MB"].get() == "0x4", \
        "MB hex failed: %r" % app.size_hex_entries["MB"].get()
    assert app.size_hex_entries["GB"].get() == "", \
        "GB hex should be blank: %r" % app.size_hex_entries["GB"].get()

    # 3b) 完整十进制（非科学计数）：3 GB + 7 字节，GB 框不得出现 'e'
    app.size_entries["B"].delete(0, tk.END)
    app.size_entries["B"].insert(0, str(3 * 1024 ** 3 + 7))
    app.convert_size_entry("B")
    assert "e" not in app.size_entries["GB"].get().lower(), \
        "GB shows scientific notation: %r" % app.size_entries["GB"].get()

    # 4) 取位字段：从 0x12345678 提取 [15:8] == 0x56
    app.decimal_output.delete(0, tk.END)
    app.decimal_output.insert(0, str(0x12345678))
    app.update_dec_btn_val_by_entry(None)
    app.entry_bit_high.delete(0, tk.END)
    app.entry_bit_high.insert(0, "15")
    app.entry_bit_low.delete(0, tk.END)
    app.entry_bit_low.insert(0, "8")
    app.extract_bit_field()
    assert app.entry_field_dec.get() == str(0x56), \
        "bit field dec failed: %r" % app.entry_field_dec.get()
    assert app.entry_field_hex.get() == "0x56", \
        "bit field hex failed: %r" % app.entry_field_hex.get()
    assert app.entry_field_bin.get() == format(0x56, '08b'), \
        "bit field bin failed: %r" % app.entry_field_bin.get()

    # 4b) 复现并验证用户反馈：0x100 的 bit8-15，高低位写反也应得到 1（不崩溃）
    app.hex_output.delete(0, tk.END)
    app.hex_output.insert(0, "0x100")
    app.update_btn_val_by_entry(None)
    app.entry_bit_high.delete(0, tk.END)
    app.entry_bit_high.insert(0, "8")     # 故意把高低位写反
    app.entry_bit_low.delete(0, tk.END)
    app.entry_bit_low.insert(0, "15")
    app.extract_bit_field()
    assert app.entry_field_dec.get() == "1", \
        "reversed-order extract failed: %r" % app.entry_field_dec.get()

    # 5) 复位与背景色切换不应抛异常（验证无残留控件引用）
    app.bit_reset()
    app.ChangeBackgroundColor("纯白")

    print("SMOKE OK")
    root.destroy()


if __name__ == '__main__':
    main()
