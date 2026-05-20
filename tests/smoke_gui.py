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

    # 3) 复位与背景色切换不应抛异常（验证无残留控件引用）
    app.bit_reset()
    app.ChangeBackgroundColor("纯白")

    print("SMOKE OK")
    root.destroy()


if __name__ == '__main__':
    main()
