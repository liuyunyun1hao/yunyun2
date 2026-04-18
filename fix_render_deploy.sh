#!/bin/bash
# 修复Render部署问题的脚本

echo "🔧 修复Render部署配置..."
echo "=============================="

# 1. 修改start.sh为可执行
chmod +x start.sh
echo "✅ 设置start.sh为可执行文件"

# 2. 更新start.sh内容
cat > start.sh << 'EOF'
#!/bin/bash
# YunYun AI Proxy 启动脚本

echo "Starting YunYun AI Proxy..."

# 激活虚拟环境（如果需要）
if [ -d "/opt/render/project/src/.venv" ]; then
    source /opt/render/project/src/.venv/bin/activate
fi

# 运行主程序
python app.py
EOF

echo "✅ 更新start.sh内容"

# 3. 创建render.yaml的正确配置
cat > render.yaml << 'EOF'
services:
  - type: web
    name: yunyun-proxy
    runtime: python
    region: singapore
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    autoDeploy: true
    branch: main
    envVars:
      - key: REQUIRE_AUTH
        value: "true"
      - key: AUTH_USERNAME
        value: "admin"
      - key: AUTH_PASSWORD
        generateValue: true
      - key: ENCRYPT_ENABLED
        value: "true"
      - key: API_BASE
        value: "https://api.siliconflow.cn/v1"
EOF

echo "✅ 更新render.yaml配置"

# 4. 确保app.py存在
if [ ! -f "app.py" ]; then
    cat > app.py << 'EOF'
#!/usr/bin/env python3
# Render兼容入口文件

import os
import sys

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入主应用
from proxy_server_render import app

if __name__ == "__main__":
    # 生产环境使用waitress
    from waitress import serve
    
    # 从环境变量获取端口，或使用默认值
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting YunYun AI Proxy on port {port}")
    
    # 启动服务
    serve(app, host="0.0.0.0", port=port)
EOF
    echo "✅ 创建app.py文件"
fi

echo ""
echo "🎯 需要执行的操作："
echo "=================="
echo "1. 上传以下文件到GitHub："
echo "   - app.py"
echo "   - proxy_server_render.py"
echo "   - requirements.txt"
echo "   - render.yaml"
echo "   - start.sh (可选)"
echo ""
echo "2. 在Render中更新Start Command："
echo "   改为：python app.py"
echo ""
echo "3. 重新部署"
echo "=============================="
echo "✅ 修复脚本完成！"