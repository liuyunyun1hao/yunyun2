#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render兼容入口文件
解决Python 3.14环境下的pkg_resources问题
"""

import os
import sys

# 将当前目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入主程序
from proxy_server_render import app

if __name__ == "__main__":
    # 始终使用生产服务器
    from waitress import serve
    
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 启动 YunYun AI 代理服务 v4.0-Cloud")
    print(f"📡 端口: {port}")
    print(f"🔒 认证要求: True")
    
    # 检查环境变量
    if not os.environ.get("AUTH_PASSWORD"):
        print("⚠️  警告: AUTH_PASSWORD未设置，请设置环境变量")
    
    # 使用生产服务器
    serve(app, host="0.0.0.0", port=port, threads=4)