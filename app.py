#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render兼容入口文件
解决Python 3.14环境下的pkg_resources问题
"""

import sys
import os

# 将当前目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入主程序
from proxy_server_render import app

if __name__ == "__main__":
    # 这是Render需要的导入
    from waitress import serve
    
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting YunYun AI Proxy on port {port}")
    serve(app, host="0.0.0.0", port=port)