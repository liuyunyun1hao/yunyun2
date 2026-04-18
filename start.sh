#!/bin/bash
# 启动脚本 - Render兼容版本
echo "🚀 启动 YunYun AI 代理服务..."

# 检查环境变量
if [ -z "$AUTH_PASSWORD" ]; then
    echo "⚠️  警告: AUTH_PASSWORD未设置，将无法进行基础认证"
    echo "请设置环境变量 AUTH_PASSWORD"
fi

# 运行app.py（主入口）
python app.py