#!/bin/bash
# YunYun AI 代理服务部署脚本

set -e

echo "🔧 YunYun AI 代理服务 Render 部署助手 🔧"
echo "========================================="

# 检查是否已安装必要的工具
if ! command -v git &> /dev/null; then
    echo "❌ 请先安装 Git"
    exit 1
fi

echo ""
echo "📦 准备部署文件..."

# 列出需要上传的文件
echo ""
echo "需要上传到GitHub的文件:"
echo "========================="
echo "1. proxy_server_render.py  (主程序)"
echo "2. requirements.txt        (Python依赖)"
echo "3. render.yaml            (Render配置)"
echo "4. README.md              (说明文档)"
echo "5. .env.example           (环境变量示例)"
echo ""
echo "🚀 部署步骤:"
echo ""
echo "🌟 第一步: 上传到 GitHub"
echo "  1. 访问 https://github.com"
echo "  2. 创建新仓库 (New repository)"
echo "  3. 将上述文件上传到仓库"
echo ""
echo "🌟 第二步: 部署到 Render"
echo "  1. 访问 https://render.com"
echo "  2. 使用GitHub账号登录"
echo "  3. 点击 'New +' → 'Blueprint'"
echo "  4. 选择你的GitHub仓库"
echo "  5. 点击 'Apply'"
echo ""
echo "🌟 第三步: 记录认证信息"
echo "  部署完成后:"
echo "  1. 在Render控制台找到你的服务"
echo "  2. 点击 'Environment' 标签页"
echo "  3. 记录 AUTH_PASSWORD 的值"
echo ""
echo "🌟 第四步: 导入密钥"
echo "  服务启动后，使用以下命令导入API密钥:"
echo ""
echo "  curl -X POST 'https://你的服务.onrender.com/api/data' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Basic \\\$(echo -n admin:你的密码 | base64)' \\"
echo '    -d '\''{
      "keys": [
        {
          "key": "sk-你的硅基流动密钥",
          "balance": "未知", 
          "fail_count": 0
        }
      ],
      "active_key": "sk-你的硅基流动密钥"
    }'\'''
echo ""
echo "========================================="
echo "✨ 部署完成！ ✨"
echo ""
echo "🔗 服务地址: https://你的服务.onrender.com"
echo "👥 用户名: admin"
echo "🔑 密码: 在Render环境变量中查看"
echo ""
echo "💡 快速测试:"
echo "  curl -X POST 'https://你的服务.onrender.com/v1/chat/completions' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'Authorization: Basic \\\$(echo -n admin:密码 | base64)' \\"
echo '    -d '\''{
      "model": "Qwen/Qwen2.5-7B-Instruct",
      "messages": [{"role": "user", "content": "你好"}],
      "stream": false
    }'\'''
echo ""
echo "📚 详细说明请查看 README.md"