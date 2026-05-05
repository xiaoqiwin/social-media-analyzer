# -*- coding: utf-8 -*-
"""
启动脚本 - 解决Trae IDE终端编码问题
"""

import os
import sys
import subprocess

# 在运行main.py之前设置UTF-8编码
if sys.platform == 'win32':
    # 设置Windows代码页为UTF-8
    subprocess.run(['cmd', '/c', 'chcp', '65001'], capture_output=True)
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 运行主程序
os.system('python main.py')
