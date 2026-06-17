#!/usr/bin/python3
# RegisterSprite  Copyright (C) 2022-2023  Robin (jiangrenbin329@gmail.com)

# This file is part of RegisterSprite
#   ____ ____  _      __     _______  ___
#  / ___|  _ \| |     \ \   / /___ / / _ \
# | |  _| |_) | |      \ \ / /  |_ \| | | |
# | |_| |  __/| |___    \ V /  ___) | |_| |
#  \____|_|   |_____|    \_/  |____(_)___/
#
# RegisterSprite is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
''''''
"""
 ____            _     _              ____             _ _
|  _ \ ___  __ _(_)___| |_ ___ _ __  / ___| _ __  _ __(_) |_ ___
| |_) / _ \/ _` | / __| __/ _ \ '__| \___ \| '_ \| '__| | __/ _ \
|  _ <  __/ (_| | \__ \ ||  __/ |     ___) | |_) | |  | | ||  __/
|_| \_\___|\__, |_|___/\__\___|_|    |____/| .__/|_|  |_|\__\___|
           |___/                           |_|

https://github.com/Robin329/register_sprite_64bit

    _    ____  __  __     _     _
   / \  |  _ \|  \/  |   | |   (_)_ __  _   ___  __
  / _ \ | |_) | |\/| |   | |   | | '_ \| | | \ \/ /
 / ___ \|  _ <| |  | |   | |___| | | | | |_| |>  <
/_/   \_\_| \_\_|  |_|   |_____|_|_| |_|\__,_/_/\_\

 _____                               _
| ____|_   _____ _ __ _   ___      _| |__   ___ _ __ ___
|  _| \ \ / / _ \ '__| | | \ \ /\ / / '_ \ / _ \ '__/ _ \
| |___ \ V /  __/ |  | |_| |\ V  V /| | | |  __/ | |  __/
|_____| \_/ \___|_|   \__, | \_/\_/ |_| |_|\___|_|  \___|
                      |___/
"""

# import **************************************************
from lib import _file_operations
from lib import _debug
from lib import _color_operations
from lib import _calc
from tkinter import messagebox
import os
import sys
import tkinter as tk
if sys.version_info[0] < 3:
    from Tkinter import *
else:
    from tkinter import *


class MyGui(Frame):
    # kv结构体
    class Namedvariable(object):
        def __init__(self, name, value):
            self.name = name
            self.value = value
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

    # 单位换算：在某个单位框输入数值并回车 -> 字节数 -> 写入寄存器
    def convert_size_entry(self, unit, event=None):
        try:
            bytes_ = self.calc.unit_to_bytes(
                self.size_entries[unit].get(), unit)
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

    # 取位字段：从当前 64 位寄存器中提取 [高位:低位] 的值并显示（含错误提示）
    def extract_bit_field(self, event=None):
        try:
            high = int(self.entry_bit_high.get().strip())
            low = int(self.entry_bit_low.get().strip())
        except ValueError:
            messagebox.showerror("错误", "位号必须为整数")
            return
        if high < low:                      # 高低位写反时自动归一，保证位宽为正
            high, low = low, high
        value = int(self.get_bin_value(mode='normal'), 2)
        try:
            field = self.calc.extract_bits(value, high, low)
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
        self._fill_field_result(field, high - low + 1)

    # 寄存器变化时静默刷新取位结果（输入非法或控件未就绪则跳过，不弹窗）
    def refresh_bit_field(self):
        try:
            high = int(self.entry_bit_high.get().strip())
            low = int(self.entry_bit_low.get().strip())
            if high < low:
                high, low = low, high
            value = int(self.get_bin_value(mode='normal'), 2)
            field = self.calc.extract_bits(value, high, low)
        except (ValueError, AttributeError):
            return
        self._fill_field_result(field, high - low + 1)

    # 将取位结果写入只读的 十进制/十六进制/二进制 显示框
    def _fill_field_result(self, field, width):
        self._set_readonly_entry(self.entry_field_dec, str(field))
        self._set_readonly_entry(self.entry_field_hex, hex(field))
        self._set_readonly_entry(
            self.entry_field_bin, format(field, '0{}b'.format(width)))

    # 写入只读 Entry：临时解锁 -> 清空 -> 写入 -> 重新锁定
    def _set_readonly_entry(self, entry, text):
        entry['state'] = 'normal'
        entry.delete(0, END)
        entry.insert(0, text)
        entry['state'] = 'readonly'

    # event end ***************************************************

    # 结构体生成函数
    def make_struct(self, name, value):
        return self.Namedvariable(name=name, value=value)

    def __init__(self, master=None):
        super().__init__(master)
        self.main_window_title = 'Register Sprite 64bit'
        self.Window = master  # 主窗体
        self.pack()

        self.flag_user_config = False  # 用户配置文件标识，False为不存在
        self.path_user_config = r'./user-config.ini'  # 用户配置文件路径
        self.fops = _file_operations.FileOperations()  # 配置文件操作
        self.fontstyle = _color_operations.FontStyle()  # 终端打印样式
        self.calc = _calc.CalcEngine()  # 计算/单位换算引擎

        self.lbl_list = []  # 按钮上label列表
        self.btn_list = []  # 位按钮列表
        self.placeholder_list = []  # 占位控件列表
        self.btn_num = 63  # 按钮顶部label字符
        # self.cpu_word_length = DWORD  # 默认CPU字长

        # 63-48 和 47-31 位按钮
        self.frame_btn_row1 = Frame(self.Window)
        self.frame_btn_row2 = Frame(self.Window)

        # 31-16 和 15-0 位按钮
        self.frame_btn_row3 = Frame(self.Window)
        self.frame_btn_row4 = Frame(self.Window)

        self.bg_color = self.make_struct('backgroundcolor', "#f0f0f0")
        self.btn_color = self.make_struct('buttoncolor', '#f3f1ef')
        self.text_color = self.make_struct('textcolor', '#000000')

        self.color_dict = {}
        self.color_dict['backgroundcolor'] = self.bg_color.value
        self.color_dict['buttoncolor'] = self.btn_color.value
        self.color_dict['textcolor'] = self.text_color.value

        # 初始化16进制字典
        self.dict_hex_after9 = {}
        self.upper_str_hex_after9 = "0123456789ABCDEF"
        lower_str_hex_after9 = self.upper_str_hex_after9.lower()
        for i in range(0, 16):
            self.dict_hex_after9[self.upper_str_hex_after9[i]] = i
            self.dict_hex_after9[lower_str_hex_after9[i]] = i

        # 初始化操作
        self.log_on = BooleanVar()
        self.log_on.set(False)
        self.log_file = os.path.join(os.getcwd()+"log", "log.txt")  # 用于存储日志的路径
        self.init_user_config()
        self.init_frame()
        self.init_menu()
        self.init_color()
        self.init_view()

        # print(self.ChangeBackgroundColor(self.bg_color))
    @_debug.printk()
    def log_print(self, text):  # 新增一个方法，用于替代 print 方法
        if self.log_on.get():  # 如果日志状态为 True，则将字符串写入日志文件，并添加换行符
            log_file = open(self.log_file, 'a')
            log_file.write(text + '\n')
            log_file.close()
        print(text)  # 无论日志状态如何，都使用 print 方法将字符串打印到控制台

    def log_write(self, text):  # 新增一个方法，用于将字符串写入日志文件
        if self.log_on.get():  # 如果日志状态为 True，则将字符串写入日志文件，并添加换行符
            try:  # 新增一个 try-except 语句，用于捕获可能发生的异常，并显示错误信息
                # 修改为使用 x 模式来创建日志文件，如果文件已存在，则抛出 FileExistsError 异常
                log_file = open(self.log_file, 'x')
                log_file.write(text + '\n')
                log_file.close()
            except FileExistsError as e:  # 新增一个异常处理语句，用于显示文件已存在的错误信息
                messagebox.showerror("错误", str(e))

    @_debug.printk()
    def init_user_config(self):
        if os.path.exists(self.path_user_config):
            self.flag_user_config = True
        else:
            print(f'{self.path_user_config}not found, creating')
            with open(self.path_user_config, 'w') as config:
                self.flag_user_config = True
                config.close()

    @_debug.printk()
    def init_frame(self):
        if self.flag_user_config:
            # 尝试获取Main窗口标题属性值
            try:
                self.main_window_title = self.fops.read_config(path=self.path_user_config,
                                                               section='Title',
                                                               key='MainWindowTitle')
                print(self.main_window_title)
            except:
                print('Title section not found! Using default window title')

            self.fops.write_config(
                self.path_user_config, 'Title', 'MainWindowTitle', self.main_window_title)
            pass
        else:
            # 将默认标题属性值写入配置文件
            self.fops.write_config(
                self.path_user_config, 'Title', 'MainWindowTitle', self.main_window_title)
            pass
        # 设置标题
        self.Window.title(self.main_window_title)

        self.frame_show = Frame(self.Window)
        self.frame_choice = Frame(self.frame_show)
        self.frame_calc = Frame(self.frame_show)
        # frame_radix 容纳“进制提示列 + 进制回显列”，整体置于上方；
        # 复选/移位/单位换算/取位等放入 frame_choice，堆叠在其下方以最小化窗口宽度
        self.frame_radix = Frame(self.frame_show)
        self.frame_label = Frame(self.frame_radix)
        self.frame_entry = Frame(self.frame_radix)

    @_debug.printk()
    def init_menu(self):
        menu_font_type = "黑体"
        menu_font_size = 10
        menu_font_tuple = (menu_font_type, menu_font_size)

        menuBar = Menu(self.Window, font=menu_font_tuple)

        self.Window.config(menu=menuBar)

        # 设置菜单
        settingBar = Menu(menuBar, tearoff=0)
        settingBar.add_command(label="背景色",
                               command=self.BackgroundColorCommand,
                               font=menu_font_tuple)

        # 文件菜单
        fileBar = Menu(menuBar, tearoff=0)
        fileBar.add_cascade(label="设置", menu=settingBar, font=menu_font_tuple)
        fileBar.add_separator()
        fileBar.add_command(
            label="退出", command=self.my_quit, font=menu_font_tuple)
        menuBar.add_cascade(label='文件', menu=fileBar, font=menu_font_tuple)

        # 日志菜单
        logBar = Menu(menuBar, tearoff=0)
        logBar.add_checkbutton(
            label="开", variable=self.log_on, command=self.logSetting, font=menu_font_tuple)
        menuBar.add_cascade(label='日志', menu=logBar, font=menu_font_tuple)

        # 帮助菜单
        helpBar = Menu(menuBar, tearoff=0)
        helpBar.add_command(label="关于", command=self.about,
                            font=menu_font_tuple)
        menuBar.add_cascade(label="帮助", menu=helpBar, font=menu_font_tuple)

    def logSetting(self):
        print("Log settings")
        logon_off = """日志打开"""
        if self.log_on.get():  # 如果日志状态为 True，则显示打开提示
            logon_off = """日志打开"""
            message = self.fontstyle.color_font(text=logon_off,
                                                display_type=7,
                                                foreground_color=32,
                                                backgroud_color=40)
            print(message)
        else:  # 如果日志状态为 False，则显示关闭提示
            logon_off = """日志关闭"""
            message = self.fontstyle.color_font(text=logon_off,
                                                display_type=7,
                                                foreground_color=31,
                                                backgroud_color=41)
            print(message)
        messagebox.showinfo("日志", logon_off)

    def my_quit(self):
        message = self.fontstyle.color_font(text="Bye",
                                            display_type=7,
                                            foreground_color=31,
                                            backgroud_color=46)
        print(message)
        self.quit()

    def about(self):
        about_info = \
            """
                寄存器小精灵 | Register Sprite 64bit
                项目地址： http://www.github.com/Robin329/register_sprite_64bit
                版本： v2023.04
            """
        messagebox.showinfo("关于", about_info)

    @_debug.printk()
    def init_color(self):
        if self.flag_user_config:
            try:
                color_dict = self.fops.read_config_section(path=self.path_user_config,
                                                           section='Color')

                for color in color_dict:
                    if color == self.bg_color.name:
                        self.bg_color.value = color_dict[color]
                        print(self.bg_color.value)
                    elif color == self.btn_color.name:
                        self.btn_color.value = color_dict[color]
                    elif color == self.text_color.name:
                        self.text_color.value = color_dict[color]
            except:
                print('Section not found.')

            self.Window.configure(bg=self.bg_color.value)
            pass
        else:
            self.fops.write_config_section(path=self.path_user_config,
                                           section='Color',
                                           data_dict=self.color_dict)
            pass

    @_debug.printk()
    def create_obj_group(self, frame, row, column):
        # 4次循环
        for i in range(4):
            lbl = tk.Label(frame,
                           background=self.bg_color.value,
                           text=self.btn_num,
                           font=("宋体", 9, "bold")
                           )
            lbl.grid(row=row,
                     column=column + i,
                     sticky=W + E + N + S, padx=3, pady=(2, 0))

            # 创建按钮
            obj = Button(frame,
                         text='0',
                         width='3',
                         height='1',
                         background=self.btn_color.value,
                         font=("宋体", 9, "bold"))

            '''
                这是for循环生成按钮，同时单独操作每个按钮的解决方案
                lambda button=obj: self_bit(button)
                这样每个按钮被点击时都会有自己独立的调用方式——将自己传给处理函数

            '''
            obj.config(command=lambda button=obj: self.set_bit(button))
            obj.grid(row=row + 1, column=column + i, padx=3, pady=(0, 4))

            # label上显示的字符减一
            self.btn_num -= 1
            # 将按钮添加到 总按钮列表用  数据更新函数会遍历列表取得二进制数据
            self.btn_list.append(obj)
            self.lbl_list.append(lbl)

    '''
        控件生成函数
    '''

    @_debug.printk()
    def init_view(self):
        '''
            这两个for循环并不涉及数据的更改和显示
            仅仅作为占位控件来使按钮易于布局
        '''
        for i in range(19):
            lbl = Label(self.frame_btn_row1,
                        background=self.bg_color.value,
                        text='  ',
                        font=("宋体", 8, "bold"))
            self.placeholder_list.append(lbl)
            lbl.grid(row=10,
                     column=i,
                     sticky=W + E + N + S, padx=7, pady=0)
        for i in range(19):
            lbl = Label(self.frame_btn_row2,
                        background=self.bg_color.value,
                        text='  ',
                        font=("宋体", 8, "bold"))
            self.placeholder_list.append(lbl)
            lbl.grid(row=10,
                     column=i,
                     sticky=W + E + N + S, padx=7, pady=0)
        for i in range(19):
            lbl = Label(self.frame_btn_row3,
                        background=self.bg_color.value,
                        text='  ',
                        font=("宋体", 8, "bold"))
            self.placeholder_list.append(lbl)
            lbl.grid(row=10,
                     column=i,
                     sticky=W + E + N + S, padx=7, pady=0)
        for i in range(19):
            lbl = Label(self.frame_btn_row4,
                        background=self.bg_color.value,
                        text='  ',
                        font=("宋体", 8, "bold"))
            self.placeholder_list.append(lbl)
            lbl.grid(row=10,
                     column=i,
                     sticky=W + E + N + S, padx=7, pady=0)

        '''第一部分用来生63-32位的label和button'''
        pad = 0
        call_mode = 0  # 用来设置是否为第一组控件
        for i in range(4):
            if call_mode == 0:
                self.create_obj_group(self.frame_btn_row1, 0, pad)
                pad += 4
                call_mode = 1  # 第一组控件生成完毕，更改标志位
            else:
                # 生成其余组控件
                self.create_obj_group(self.frame_btn_row1, 0, pad + 1)
                pad += 5

        # 将第一部分控件pack
        self.frame_btn_row1.pack(side=TOP)
        self.frame_btn_row1.configure(bg=self.bg_color.value)
        '''第二部分用来生成15-0位的label和button， 相关解释看第一部分'''
        pad = 0
        call_mode = 0
        for i in range(4):
            if call_mode == 0:
                self.create_obj_group(self.frame_btn_row2, 2, pad)
                pad += 4
                call_mode = 1
            else:
                self.create_obj_group(self.frame_btn_row2, 2, pad + 1)
                pad += 5

        # 将第一部分控件pack
        self.frame_btn_row2.pack(side=TOP)
        self.frame_btn_row2.configure(bg=self.bg_color.value)

        '''第一部分用来生成31-16位的label和button'''
        pad = 0
        call_mode = 0  # 用来设置是否为第一组控件
        for i in range(4):
            if call_mode == 0:
                self.create_obj_group(self.frame_btn_row3, 0, pad)
                pad += 4
                call_mode = 1  # 第一组控件生成完毕，更改标志位
            else:
                # 生成其余组控件
                self.create_obj_group(self.frame_btn_row3, 0, pad + 1)
                pad += 5

        # 将第一部分控件pack
        self.frame_btn_row3.pack(side=TOP)
        self.frame_btn_row3.configure(bg=self.bg_color.value)

        '''第二部分用来生成15-0位的label和button， 相关解释看第一部分'''
        pad = 0
        call_mode = 0
        for i in range(4):
            if call_mode == 0:
                self.create_obj_group(self.frame_btn_row4, 2, pad)
                pad += 4
                call_mode = 1
            else:
                self.create_obj_group(self.frame_btn_row4, 2, pad + 1)
                pad += 5

        # 将第二部分控件pack
        self.frame_btn_row4.pack(side=TOP)
        self.frame_btn_row4.configure(bg=self.bg_color.value)

        '''
        以下代码用来创建下半部分空间，包括x进制的label、Entry和复选框功能区
        frame_show继承自Window

        frame_label用来存放进制的提示区
        frame_entry用来存放进制的回显区
        frame_calc用来计算'+','-','*','/'
        frame_choice用来存放复选功能
        以上三者继承自frame_show
        '''

        self.frame_show.pack()
        self.frame_show.configure(bg=self.bg_color.value)

        # 进制label区
        self.hex = Label(self.frame_label,
                         background=self.bg_color.value,
                         text="16进制",
                         font=("宋体", 12, "bold"))
        self.hex.pack(side=TOP)
        self.decimal = Label(self.frame_label,
                             background=self.bg_color.value,
                             text="10进制",
                             font=("宋体", 12, "bold"))
        self.decimal.pack(side=TOP)
        self.octal = Label(self.frame_label,
                           background=self.bg_color.value,
                           text="8进制",
                           font=("宋体", 12, "bold"))
        self.octal.pack(side=TOP)
        self.binary = Label(self.frame_label,
                            background=self.bg_color.value,
                            text="2进制",
                            font=("宋体", 12, "bold"))
        self.binary.pack(side=TOP)

        # 进制换算区
        self.hex_output = Entry(self.frame_entry,
                                background='#f0f0f0',
                                width=40,
                                font=("宋体", 12, "bold"))
        self.hex_output.bind('<Return>', func=self.update_btn_val_by_entry)
        self.hex_output.bind('<Escape>', func=self.bit_reset)
        self.hex_output.pack(side=TOP)

        self.decimal_output = Entry(self.frame_entry,
                                    background='#f0f0f0',
                                    width=40,
                                    font=("宋体", 12, "bold"))
        self.decimal_output.bind(
            '<Return>', func=self.update_dec_btn_val_by_entry)
        self.decimal_output.bind('<Escape>', func=self.bit_reset)
        self.decimal_output.pack(side=TOP)

        self.octal_output = Entry(self.frame_entry,
                                  background='#f0f0f0',
                                  width=40,
                                  font=("宋体", 12, "bold"))
        # self.octal_output.bind('<Return>', func=self.update_btn_val_by_entry)
        self.octal_output.pack(side=TOP)

        self.binary_output = Entry(self.frame_entry,
                                   background='#f0f0f0',
                                   width=40,
                                   font=("宋体", 12, "bold"))
        # self.binary_output.bind('<Return>
        self.binary_output.pack(side=TOP)

        '''
            拓展功能区，主要拓展如下
            十六进制以位位移形式显示
        '''
        # 置位
        self.label_hex_shift_set = Label(self.frame_label,
                                         background=self.bg_color.value,
                                         text="置位",
                                         font=("宋体", 10))
        self.label_hex_shift_set.pack(side=TOP, pady=5)

        self.entry_hex_shift_set = Entry(self.frame_entry,
                                         background='#f0f0f0',
                                         width=45,
                                         font=("宋体", 10, "bold"))
        self.entry_hex_shift_set.pack(side=TOP, pady=5)

        # 清零
        self.label_hex_shift_clear = Label(self.frame_label,
                                           background=self.bg_color.value,
                                           text="清零",
                                           font=("宋体", 10))

        self.label_hex_shift_clear.pack(side=TOP)

        self.entry_hex_shift_clear = Entry(self.frame_entry,
                                           background='#f0f0f0',
                                           width=45,
                                           font=("宋体", 10, "bold"))
        self.entry_hex_shift_clear.pack(side=TOP)

        self.frame_label.pack(side=LEFT)
        self.frame_entry.pack(side=LEFT)
        # 进制区放在下半部分左列；frame_choice 之后 pack 到右列，两列并排以压缩高度
        self.frame_radix.pack(side=LEFT, anchor='n', padx=(0, 12))

        self.frame_label.configure(bg=self.bg_color.value)
        self.frame_entry.configure(bg=self.bg_color.value)
        self.frame_radix.configure(bg=self.bg_color.value)

        self.init_value()

        # 这里创建复选框功能区
        self.CheckVar = IntVar()
        self.ck_btn = Checkbutton(self.frame_choice,
                                  text="窗口保持在全屏幕的顶部",
                                  background=self.bg_color.value,
                                  variable=self.CheckVar,
                                  onvalue=1, offvalue=0,
                                  command=self.isChecked)
        self.ck_btn.pack(side=TOP)

        self.pro_btn_frame = Frame(self.frame_choice)
        # 左移功能按钮
        self.lsh_btn = Button(self.pro_btn_frame,
                              background=self.btn_color.value,
                              text="左移")
        self.lsh_btn.config(command=self.left_shift)
        self.lsh_btn.pack(side=LEFT)

        # 右移功能按键
        self.rsh_btn = Button(self.pro_btn_frame,
                              background=self.btn_color.value,
                              text="右移")
        self.rsh_btn.config(command=self.right_shift)
        self.rsh_btn.pack(side=LEFT)

        # 移位位数输入框：手动填写左移/右移多少 bit（默认 1，回车按左移执行）
        self.label_shift_bits = Label(self.pro_btn_frame,
                                      background=self.bg_color.value,
                                      text="位数",
                                      font=("宋体", 9, "bold"))
        self.label_shift_bits.pack(side=LEFT, padx=(6, 2))
        self.entry_shift_bits = Entry(self.pro_btn_frame,
                                      background='#f0f0f0',
                                      width=4,
                                      font=("宋体", 10, "bold"))
        self.entry_shift_bits.insert(0, '1')
        self.entry_shift_bits.pack(side=LEFT, padx=(0, 6))

        # 求非功能按键
        self.not_btn = Button(self.pro_btn_frame,
                              background=self.btn_color.value,
                              text="求非")
        self.not_btn.config(command=self.calc_not)
        self.not_btn.pack(side=LEFT)

        # 复位功能按键
        self.rst_btn = Button(self.pro_btn_frame,
                              background=self.btn_color.value,
                              text="复位")
        self.rst_btn.config(command=self.bit_reset)
        self.rst_btn.pack(side=LEFT)

        self.pro_btn_frame.pack(side=TOP)

        # 单位换算区：B/KB/MB/GB/TB 任一框均可直接输入，回车自动换算并刷新
        self.frame_data_size = Frame(self.frame_choice)
        self.label_unit_input = Label(self.frame_data_size,
                                      background=self.bg_color.value,
                                      text="单位换算（输入后回车）",
                                      font=("宋体", 9, "bold"))
        self.label_unit_input.pack(side=TOP, pady=(0, 3))
        # 列标题：左列十进制（可输入回车换算），右列十六进制（只读，仅整数单位有值）
        row_unit_head = Frame(self.frame_data_size)
        Label(row_unit_head, background=self.bg_color.value, text='',
              width=4, font=("宋体", 9, "bold")).pack(side=LEFT)
        Label(row_unit_head, background=self.bg_color.value, text="十进制",
              width=22, font=("宋体", 9, "bold")).pack(side=LEFT)
        Label(row_unit_head, background=self.bg_color.value, text="十六进制",
              width=16, font=("宋体", 9, "bold")).pack(side=LEFT, padx=(4, 0))
        row_unit_head.configure(bg=self.bg_color.value)
        row_unit_head.pack(side=TOP, anchor='e')
        self.size_entries = {}        # 十进制输入框（可编辑）
        self.size_hex_entries = {}    # 十六进制显示框（只读）
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
            # 在该单位框回车 -> 按此单位换算（u=unit 锁定当前循环变量）
            ent.bind('<Return>',
                     lambda e, u=unit: self.convert_size_entry(u, e))
            # 十六进制显示栏：只读，仅当该单位换算为整数时有值，否则留空
            hex_ent = Entry(row, background='#f0f0f0', width=16,
                            font=("宋体", 11, "bold"))
            hex_ent.pack(side=LEFT, padx=(4, 0))
            hex_ent.insert(0, '0x0')
            hex_ent['state'] = 'readonly'
            row.configure(bg=self.bg_color.value)
            row.pack(side=TOP, anchor='e')
            self.size_entries[unit] = ent
            self.size_hex_entries[unit] = hex_ent
        self.frame_data_size.configure(bg=self.bg_color.value)
        self.frame_data_size.pack(side=TOP, pady=5, anchor='e')

        # 取位字段区：从 64 位寄存器中提取 [高位:低位] 的值
        self.frame_bit_field = Frame(self.frame_choice)
        Label(self.frame_bit_field, background=self.bg_color.value,
              text="取位字段（高位:低位，回车或点“提取”）",
              font=("宋体", 9, "bold")).pack(side=TOP, pady=(8, 3))

        row_bit_in = Frame(self.frame_bit_field)
        Label(row_bit_in, background=self.bg_color.value, text="高位",
              font=("宋体", 9, "bold")).pack(side=LEFT)
        self.entry_bit_high = Entry(row_bit_in, background='#f0f0f0', width=4,
                                    font=("宋体", 10, "bold"))
        self.entry_bit_high.insert(0, '63')
        self.entry_bit_high.bind('<Return>', self.extract_bit_field)
        self.entry_bit_high.pack(side=LEFT, padx=(2, 8))
        Label(row_bit_in, background=self.bg_color.value, text="低位",
              font=("宋体", 9, "bold")).pack(side=LEFT)
        self.entry_bit_low = Entry(row_bit_in, background='#f0f0f0', width=4,
                                   font=("宋体", 10, "bold"))
        self.entry_bit_low.insert(0, '0')
        self.entry_bit_low.bind('<Return>', self.extract_bit_field)
        self.entry_bit_low.pack(side=LEFT, padx=(2, 8))
        self.btn_extract = Button(row_bit_in, background=self.btn_color.value,
                                  text="提取", command=self.extract_bit_field)
        self.btn_extract.pack(side=LEFT)
        row_bit_in.configure(bg=self.bg_color.value)
        row_bit_in.pack(side=TOP, pady=2)

        # 结果显示：十进制 / 十六进制 / 二进制（只读）
        self.entry_field_dec = self._make_field_result_row(
            self.frame_bit_field, "十进制")
        self.entry_field_hex = self._make_field_result_row(
            self.frame_bit_field, "十六进制")
        self.entry_field_bin = self._make_field_result_row(
            self.frame_bit_field, "二进制")

        self.frame_bit_field.configure(bg=self.bg_color.value)
        self.frame_bit_field.pack(side=TOP, pady=5)
        # 复选框/功能区作为下半部分右列，与进制区并排，压缩整体高度
        self.frame_choice.pack(side=LEFT, anchor='n')
        self.frame_choice.configure(bg=self.bg_color.value)
        self.refresh_bit_field()    # 初始化取位结果显示（默认 63:0）

    # 生成一行“标签 + 只读结果框”，返回该 Entry
    def _make_field_result_row(self, parent, label_text):
        row = Frame(parent)
        Label(row, background=self.bg_color.value, text=label_text,
              width=7, anchor='e', font=("宋体", 9, "bold")).pack(side=LEFT)
        ent = Entry(row, background='#f0f0f0', width=28,
                    font=("宋体", 10, "bold"))
        ent.insert(0, '0')
        ent.pack(side=LEFT)             # 必须 pack，否则结果框不显示
        ent['state'] = 'readonly'
        row.configure(bg=self.bg_color.value)
        row.pack(side=TOP, anchor='e', pady=1)
        return ent

    @_debug.printk()
    def CWL_change(self, cwl):
        print("CPU WORD LENGTH: ", cwl)
        pass

    '''
        数据初始化函数
    '''

    @_debug.printk()
    def init_value(self):
        # 这部分代码用来向回显区插入初始数据，并无实际作用
        self.binary_output['state'] = 'normal'
        self.hex_output.insert(0, '0x0000000000000000')
        self.decimal_output.insert(0, '0')
        self.octal_output.insert(0, '0o0')
        self.binary_output['state'] = 'normal'
        self.binary_output.insert(
            0, '0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000')
        self.binary_output['state'] = 'readonly'

        self.entry_hex_shift_set.insert(0, '0')
        self.entry_hex_shift_clear.insert(0, '0')
        self.binary_output['state'] = 'readonly'

        # 复位时恢复单位换算区与取位结果（启动首次调用时这些控件尚未创建，故 hasattr 保护）
        if hasattr(self, 'size_entries'):
            for unit, ent in self.size_entries.items():
                ent.delete(0, END)
                ent.insert(0, '0')
                self._set_readonly_entry(self.size_hex_entries[unit], '0x0')
        if hasattr(self, 'entry_field_dec'):
            self.refresh_bit_field()
    '''
        数据清除函数
    '''

    @_debug.printk()
    def clear_value(self):
        '''清空各进制回显区，每次修改前都要先清空'''
        self.binary_output['state'] = 'normal'
        self.hex_output.delete(0, END)
        self.decimal_output.delete(0, END)
        self.octal_output.delete(0, END)
        self.binary_output.delete(0, END)

        self.entry_hex_shift_set.delete(0, END)
        self.entry_hex_shift_clear.delete(0, END)
        for ent in self.size_entries.values():
            ent.delete(0, END)
        for ent in self.size_hex_entries.values():
            self._set_readonly_entry(ent, '')
        self.binary_output['state'] = 'readonly'

    '''
        show_data 数据显示函数
        该函数用来将按钮数据处理后显示到进制换算区
    '''

    @_debug.printk()
    def show_data(self):
        self.clear_value()
        self.binary_output['state'] = 'normal'  # 将二进制回显区设置为可写

        # 初始化
        _bin = self.get_bin_value(mode='normal')
        not_bin = self.get_bin_value(mode='not')
        _oct = ''
        _hex = ''
        bin_show = self.get_bin_value(mode='show')

        # 进制转换
        dec = int(_bin, 2)
        not_dec = int(not_bin, 2)
        _hex = hex(dec)
        not_hex = hex(not_dec)
        '''
            直接使用hex()函数会得到一个这样的数据 0x7
            而我们要显示这样的                   0x00000007
            其实两者相等，只不过后者更加便于查看
        '''
        temp_str = ''  # 临时字符串，用来存放0
        temp_str_not = ''
        # 根据hex()得到最低为3位的数据，可以得出0的个数，累加到temp_str中
        for n in range(10 - len(_hex)):
            temp_str += '0'

        # 拼接字符串，以'x'隔开字符串，取后半部分
        # 0x + n0(n=7) + 0x7.split('x')[1] 等于 7 即 0x00000007
        _hex = '0x' + temp_str + _hex.split('x')[1]
        not_hex = '0x' + temp_str_not + not_hex.split('x')[1]

        # 得到8进制数据
        _oct = oct(dec)

        '''
            进阶功能区数据处理
            这部分的思路是将二进制数据每四个分为一组处理，64位模式下共16组
            这里并没有考虑其他字长模式cpu的情况，后期如果添加其他字长模式要修改这部分代码
        '''
        # 置位数据处理
        hex_bit_dict = {}  # 总16进制数据字典
        hex_bit_list = bin_show.split(' ')[:16]
        bit_index = 15  # 64位模式  16组4位二进制数据

        # 遍历列表将数据以如下形式保存到字典中
        # 7:0000  6:0000
        for hex_bit in hex_bit_list:
            hex_bit_dict[bit_index] = hex_bit
            bit_index -= 1

        # 获取有效值，即不为0的组
        current_value_dict = {}  # 有效值字典

        # 遍历上一步得到的字典，得到有效值字典
        for key in hex_bit_dict:
            if hex_bit_dict[key] != '0000':
                current_value_dict[key] = hex_bit_dict[key]

        # 获得字典长度，后边判断显示格式会用到
        len_current_value_dict = len(current_value_dict)

        # 要拼接显示的到置位区的字符串，格式如下
        # （1 << 10） | (3 << 12)
        current_value_str = ''

        # 根据字典长度处理字符串格式
        if len_current_value_dict == 1:
            for pkey in current_value_dict:
                current_hex_value = hex(int(current_value_dict[pkey], 2))
                current_value_str += '({0}<<{1})'.format(
                    current_hex_value, pkey * 4)
        elif len_current_value_dict > 1:
            for pkey in current_value_dict:
                current_hex_value = hex(int(current_value_dict[pkey], 2))
                current_value_str += '|({0}<<{1})'.format(
                    current_hex_value, pkey * 4)
            current_value_str = current_value_str[1:]
        else:
            pass

        # 清零数据处理在遍历按钮和进制转换时已经处理完成

        '''
            更新数据
        '''
        self.hex_output.insert(0, _hex)
        self.decimal_output.insert(0, dec)
        self.octal_output.insert(0, _oct)
        self.binary_output.insert(0, bin_show)

        # 更新进阶功能区
        self.entry_hex_shift_set.insert(0, current_value_str)
        self.entry_hex_shift_clear.insert(0, not_hex)

        # 数据大小：寄存器值视为字节数，同步刷新各单位十进制框 + 十六进制栏
        units = self.calc.bytes_to_units(dec)
        units_hex = self.calc.bytes_to_units_hex(dec)
        for unit in self.calc.UNITS:
            self.size_entries[unit].delete(0, END)
            self.size_entries[unit].insert(0, units[unit])
            self._set_readonly_entry(self.size_hex_entries[unit], units_hex[unit])
        self.binary_output['state'] = 'readonly'  # 将二进制回显区设置为只读
        self.refresh_bit_field()    # 取位结果随寄存器变化刷新

    '''
        按钮每次点击都会调用该函数，执行完样式更改后调用数据更新函数
    '''

    @_debug.printk()
    def set_bit(self, obj):

        # 根据按钮值更改按钮显示信息
        if obj['text'] == '0':
            obj.config(text='1')
        elif obj['text'] == '1':
            obj.config(text='0')

        # 调用数据更新函数
        self.update_btn_style()
        self.show_data()

    '''
        mode
            normal : 二进制数据
            not    : 求非后的二进制数据
            bin_show  :  用于显示给用户的二进制数据
    '''

    @_debug.printk()
    def get_bin_value(self, mode):
        # 遍历按钮数组，将按钮值拼接为字符串，得到一个二进制数据
        # _bin为初始数据
        # bin_show为显示到回显区的数据，因为便于查看，每隔4位插入了一个空格，不能用于进制转换,仅作显示
        _bin = ''
        not_bin = ''
        bin_show = ''
        space_cnt = 0

        for i in self.btn_list:
            if i['text'] == '1':
                _bin += i['text']
                bin_show += i['text']
                not_bin += '0'
                space_cnt += 1
            elif i['text'] == '0':
                _bin += i['text']
                bin_show += i['text']
                not_bin += '1'
                space_cnt += 1

            if space_cnt == 4:
                bin_show += ' '
                space_cnt = 0

        if mode == 'normal':
            return _bin
        elif mode == 'not':
            return not_bin
        else:
            return bin_show

    '''
        按钮样式更新函数
    '''

    @_debug.printk()
    def update_btn_style(self):
        for btn in self.btn_list:
            if btn['text'] == '0':
                btn.config(relief='raised')  # 设置按钮样式为升起
                btn.config(bg='#f0f0f0')
            else:
                btn.config(relief='sunken')  # 设置按钮样式为按下
                btn.config(bg='gray')

    '''
        复位功能函数
    '''

    @_debug.printk()
    def bit_reset(self, event=None):
        # 遍历按钮列表，将按钮恢复至初始状态，即数值0样式为升起
        for btn in self.btn_list:
            btn.config(text='0')

        self.update_btn_style()
        '''
            复位的数据处理其实可以有很多种方法，这里提供了两种
            1.先清除显示区，再插入初始值
            2.直接调用show_data()函数处理按钮数据
            两种方法最终效果都差不多，但是前者的资源开销应该小一点
        '''
        self.clear_value()  # 清除数据
        self.init_value()  # 初始化数据
        # self.show_data()

    '''
        求非功能函数
    '''

    @_debug.printk()
    def calc_not(self):
        # 遍历按钮列表,反转按钮值和样式
        for btn in self.btn_list:
            if btn['text'] == '0':
                btn.config(text='1')
            else:
                btn.config(text='0')

        self.update_btn_style()
        # 这里直接调用数据处理显示函数就行了
        self.show_data()

    '''
        左右移位功能
    '''

    # 读取“位数”输入框，返回 0~64 的移位位数；非法输入弹窗提示并返回 None
    def _get_shift_bits(self):
        text = self.entry_shift_bits.get().strip()
        try:
            bits = int(text)
        except ValueError:
            messagebox.showerror("错误", "移位位数必须为整数")
            return None
        if bits < 0 or bits > 64:
            messagebox.showerror("错误", "移位位数必须在 0~64 之间")
            return None
        return bits

    # 按指定方向移位（'left'/'right'），位数取自“位数”输入框
    def _do_shift(self, direction):
        bits = self._get_shift_bits()
        if bits is None:
            return
        value = int(self.get_bin_value(mode='normal'), 2)
        result = self.calc.shift(value, bits, direction)
        self.set_register_bits(result)
        self.show_data()

    @_debug.printk()
    def left_shift(self):
        self._do_shift('left')

    @_debug.printk()
    def right_shift(self):
        self._do_shift('right')

    '''
        窗口置顶函数
    '''

    @_debug.printk()
    # 窗口置顶复选框调用函数
    def isChecked(self):
        val = self.CheckVar.get()
        if val == 1:
            # 窗口保持在全屏幕的顶部
            self.Window.attributes("-toolwindow", 1)
            self.Window.wm_attributes("-topmost", 1)
        else:
            # 取消 窗口保持在全屏幕的顶部
            self.Window.attributes("-toolwindow", 0)
            self.Window.wm_attributes("-topmost", 0)

    @_debug.printk()
    # 背景色切换窗口生成函数
    def askColorInfo(self):
        color_input = _color_operations.ColorChoiceFrame(master=self.Window)
        self.Window.wait_window(color_input)
        # print(color_input.color_data_list)
        return color_input.current_btn_value

    @_debug.printk()
    # 代码复用，作用是遍历列表，设置背景色
    def TraverseTargetList(self, list_):
        for obj in list_:
            obj.config(bg=self.bg_color.value)

    @_debug.printk()
    # 菜单项背景色调用函数
    def BackgroundColorCommand(self):
        # 拉起颜色选择窗口
        target_color = self.askColorInfo()
        print(target_color)
        if target_color != "None":
            self.ChangeBackgroundColor(target_color)

    @_debug._timeit
    # 背景色切换函数
    def ChangeBackgroundColor(self, color):
        '''
            @author: Robin
        :param color: 用户将要切换的背景颜色
        :return: 程序执行状态
        '''
        err = 1
        try:
            # 窗体背景颜色更换
            self.bg_color.value = _color_operations.GetColor(color)
            # 将背景颜色写入配置文件
            self.fops.write_config(path=self.path_user_config,
                                   section='Color',
                                   key='BackGroundColor',
                                   value=self.bg_color.value)

            # 背景颜色更换操作
            self.Window.configure(bg=self.bg_color.value)
            self.frame_btn_row1.configure(bg=self.bg_color.value)
            self.frame_btn_row2.configure(bg=self.bg_color.value)
            self.frame_btn_row3.configure(bg=self.bg_color.value)
            self.frame_btn_row4.configure(bg=self.bg_color.value)
            self.frame_label.configure(bg=self.bg_color.value)
            self.frame_show.configure(bg=self.bg_color.value)
            self.frame_entry.configure(bg=self.bg_color.value)
            self.frame_radix.configure(bg=self.bg_color.value)
            self.frame_choice.configure(bg=self.bg_color.value)

            # label及占位符背景颜色更换
            self.TraverseTargetList(self.lbl_list)
            self.TraverseTargetList(self.placeholder_list)

            # 进制label背景颜色更换
            self.hex.config(bg=self.bg_color.value)
            self.octal.config(bg=self.bg_color.value)
            self.decimal.config(bg=self.bg_color.value)
            self.binary.config(bg=self.bg_color.value)

            # 置位及清零label背景颜色更换
            self.label_hex_shift_set.config(bg=self.bg_color.value)
            self.label_hex_shift_clear.config(bg=self.bg_color.value)

            # 移位位数label背景颜色更换
            self.label_shift_bits.config(bg=self.bg_color.value)

            # checkbox背景颜色更换
            self.ck_btn.config(bg=self.bg_color.value)

            # 数据大小/单位换算背景色更换
            self.frame_data_size.config(bg=self.bg_color.value)
            for child in self.frame_data_size.winfo_children():
                child.config(bg=self.bg_color.value)
                for sub in child.winfo_children():
                    if isinstance(sub, Label):
                        sub.config(bg=self.bg_color.value)

            # 取位字段区背景色更换
            self.frame_bit_field.config(bg=self.bg_color.value)
            for child in self.frame_bit_field.winfo_children():
                child.config(bg=self.bg_color.value)
                for sub in child.winfo_children():
                    if isinstance(sub, Label):
                        sub.config(bg=self.bg_color.value)

            return err
        except:
            return -err


@_debug.printk()
def main():
    root = Tk()
    # 设置窗口大小不可更改
    root.resizable(0, 0)

    # 适配高分屏下程序界面、字体模糊
    # 注意以下设置仅适用于windows系统
    # 调用api设置成由应用程序缩放
    # ctypes.windll.shcore.SetProcessDpiAwareness(1)
    # # 调用api获得当前的缩放因子
    # ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    # # 设置缩放因子
    # root.tk.call('tk', 'scaling', ScaleFactor / 75)

    app = MyGui(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
