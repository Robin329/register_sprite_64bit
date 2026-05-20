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
