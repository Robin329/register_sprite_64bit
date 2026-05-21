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
    @file: build.py
    @author: Robin
    @version: v1.0
    @date: 2026-05-20
    @brief: 将 Register Sprite 64bit 打包为独立 Windows exe（基于 PyInstaller）
'''

import argparse
import os
import subprocess
import sys

# 路径（全部相对本脚本所在目录，双击/任意 cwd 运行都正确）
ROOT = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(ROOT, 'main.py')
ICON_PATH = os.path.join(ROOT, 'assets', 'chip.ico')
PNG_PATH = os.path.join(ROOT, 'img', 'pic.png')
DIST_DIR = os.path.join(ROOT, 'bin')      # exe 输出目录
BUILD_DIR = os.path.join(ROOT, 'build')   # PyInstaller 工作目录（已在 .gitignore）

# 生成图标时使用的多尺寸
ICON_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48),
              (64, 64), (128, 128), (256, 256)]


def check_pyinstaller():
    '''确认 PyInstaller 可用，缺失时打印安装指引并返回 False'''
    try:
        import PyInstaller  # noqa: F401
        return True
    except ImportError:
        print("[ERROR] 未找到 PyInstaller，无法打包。请先安装：")
        print("    %s -m pip install pyinstaller" % sys.executable)
        return False


def ensure_icon(use_icon):
    '''返回可用的 .ico 路径；必要时用 Pillow 从 png 生成。无法获得时返回 None'''
    if not use_icon:
        return None
    if os.path.exists(ICON_PATH):
        print("[icon] 使用已有图标：%s" % ICON_PATH)
        return ICON_PATH
    if not os.path.exists(PNG_PATH):
        print("[icon] 未找到 %s，将不使用图标。" % PNG_PATH)
        return None
    try:
        from PIL import Image
    except ImportError:
        print("[icon] 未安装 Pillow，无法从 png 生成图标，将不使用图标。")
        print("       如需图标：%s -m pip install pillow" % sys.executable)
        return None
    os.makedirs(os.path.dirname(ICON_PATH), exist_ok=True)
    with Image.open(PNG_PATH) as img:
        img.convert("RGBA").save(ICON_PATH, format='ICO', sizes=ICON_SIZES)
    print("[icon] 已从 %s 生成 %s" % (PNG_PATH, ICON_PATH))
    return ICON_PATH


def build(args):
    '''调用 PyInstaller 打包，返回退出码（0 为成功）'''
    if not os.path.exists(MAIN_PY):
        print("[ERROR] 未找到入口文件：%s" % MAIN_PY)
        return 1

    icon = ensure_icon(not args.no_icon)

    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '-y',
           '--name', args.name,
           '--distpath', DIST_DIR,
           '--workpath', BUILD_DIR,
           '--specpath', BUILD_DIR]
    cmd.append('--onedir' if args.onedir else '--onefile')
    cmd.append('--console' if args.console else '--windowed')
    if icon:
        cmd += ['--icon', icon]
    cmd.append(MAIN_PY)

    print("[build] 运行：%s" % ' '.join(cmd))
    ret = subprocess.call(cmd, cwd=ROOT)
    if ret != 0:
        print("[ERROR] PyInstaller 打包失败，退出码 %d" % ret)
        return ret

    if args.onedir:
        out = os.path.join(DIST_DIR, args.name, args.name + '.exe')
    else:
        out = os.path.join(DIST_DIR, args.name + '.exe')
    if os.path.exists(out):
        size_mb = os.path.getsize(out) / (1024 * 1024)
        print("\n[OK] 打包完成：%s (%.1f MB)" % (out, size_mb))
        return 0
    print("[WARN] 打包结束但未找到预期产物：%s" % out)
    return 1


def main():
    parser = argparse.ArgumentParser(
        description="将 Register Sprite 64bit 打包为独立 Windows exe")
    parser.add_argument('--name', default='register_sprite_64bit',
                        help='exe 名称（默认 register_sprite_64bit，与项目/常用运行名一致）')
    parser.add_argument('--onedir', action='store_true',
                        help='打包为文件夹而非单文件（启动更快）')
    parser.add_argument('--console', action='store_true',
                        help='保留控制台窗口（调试用）')
    parser.add_argument('--no-icon', action='store_true',
                        help='不使用图标')
    args = parser.parse_args()

    if not check_pyinstaller():
        sys.exit(1)
    sys.exit(build(args))


if __name__ == '__main__':
    main()
