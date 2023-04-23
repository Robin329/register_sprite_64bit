```python
import tkinter as tk

# 创建一个 Tkinter 窗口
root = tk.Tk()
root.title("计算器")

# 定义全局变量以进行计算
expression = ""

# 用于将数字添加到计算表达式的函数
def add_to_expression(num):
    global expression
    expression += str(num)
    equation.set(expression)

# 计算表达式的函数
def evaluate_expression():
    global expression
    try:
        result = str(eval(expression))
        equation.set(result)
        expression = ""
    except:
        equation.set("错误")
        expression = ""

# 清除表达式的函数
def clear_expression():
    global expression
    expression = ""
    equation.set("")

# 创建一个 Tkinter 字符串变量以显示表达式和结果
equation = tk.StringVar()
expression_field = tk.Entry(root, textvariable=equation)

# 创建数字按钮
button_1 = tk.Button(root, text="1", command=lambda: add_to_expression(1))
button_2 = tk.Button(root, text="2", command=lambda: add_to_expression(2))
button_3 = tk.Button(root, text="3", command=lambda: add_to_expression(3))
button_4 = tk.Button(root, text="4", command=lambda: add_to_expression(4))
button_5 = tk.Button(root, text="5", command=lambda: add_to_expression(5))
button_6 = tk.Button(root, text="6", command=lambda: add_to_expression(6))
button_7 = tk.Button(root, text="7", command=lambda: add_to_expression(7))
button_8 = tk.Button(root, text="8", command=lambda: add_to_expression(8))
button_9 = tk.Button(root, text="9", command=lambda: add_to_expression(9))
button_0 = tk.Button(root, text="0", command=lambda: add_to_expression(0))

# 创建运算符按钮
button_plus = tk.Button(root, text="+", command=lambda: add_to_expression("+"))
button_minus = tk.Button(root, text="-", command=lambda: add_to_expression("-"))
button_multiply = tk.Button(root, text="×", command=lambda: add_to_expression("*"))
button_divide = tk.Button(root, text="÷", command=lambda: add_to_expression("/"))
button_equal = tk.Button(root, text="=", command=evaluate_expression)
button_clear = tk.Button(root, text="清除", command=clear_expression)

# 将计算表达式输入框和按钮添加到窗口
expression_field.grid(columnspan=4, ipadx=70)
button_1.grid(row=2, column=0)
button_2.grid(row=2, column=1)
button_3.grid(row=2, column=2)
button_plus.grid(row=2, column=3)
button_4.grid(row=3, column=0)
button_5.grid(row=3, column=1)
button_6.grid(row=3, column=2)
button_minus.grid(row=3, column=3)
button_7.grid(row=4, column=0)
button_8.grid(row=4, column=1)
button_9.grid(row=4, column=2)
button_multiply.grid(row=4, column=3)
button_0.grid(row=5, column=0)
button_clear.grid(row=5, column=1)
button_divide.grid(row=5, column=2)
button_equal.grid(row=5, column=3)
root.mainloop()

```
