import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from proxy_server_render import app
from waitress import serve

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ YunYun Proxy 启动成功，端口: {port}")
    serve(app, host="0.0.0.0", port=port, threads=4)