# -*- coding: utf-8 -*-
"""
WSGI入口文件
用于Render等云平台的生产环境部署
"""

import os
import sys

# 添加项目目录到Python路径
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# 从ai_server导入Flask应用
from ai_server import app

# 生产环境配置
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
