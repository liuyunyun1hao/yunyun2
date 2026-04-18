#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YunYun AI 代理服务 (云端部署 Render 优化版)
支持硅基流动API代理、智能密钥轮询、密钥保护与访问控制
专为Render免费部署优化
"""

import os
import sys
import json
import time
import logging
import logging.handlers
from pathlib import Path
from flask import Flask, request, jsonify, Response, render_template_string
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import requests

# 尝试导入加密库（可选）
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ========== 配置 ==========
# 从环境变量读取配置，否则使用默认值
VERSION = "4.0-Cloud"
API_BASE = os.environ.get("API_BASE", "https://api.siliconflow.cn/v1")

# 端口配置 (Render会自动设置PORT环境变量)
PORT = int(os.environ.get("PORT", 5000))

# 数据存储配置
# Render免费版重启会清空本地文件，所以提供两种选择：
# 1. 使用环境变量存储（推荐，但需要手动设置）
# 2. 使用临时文件（重启会丢失）
USE_ENV_STORAGE = os.environ.get("USE_ENV_STORAGE", "false").lower() == "true"
ENCRYPT_ENABLED = os.environ.get("ENCRYPT_ENABLED", "true").lower() == "true"

# 访问控制配置
# 基本认证用户名密码（从环境变量读取）
AUTH_USERNAME = os.environ.get("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "")
REQUIRE_AUTH = os.environ.get("REQUIRE_AUTH", "true").lower() == "true"

# 也可以设置API密钥认证（更简单）
API_KEY = os.environ.get("API_KEY", "")
USE_API_KEY_AUTH = os.environ.get("USE_API_KEY_AUTH", "false").lower() == "true"

# 文件路径
LOG_FILE = "proxy.log"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB (Render免费版限制)
LOG_BACKUP_COUNT = 1
ENCRYPT_KEY_FILE = "encrypt.key"
DATA_FILE = "keys_data.json"

# 故障转移配置
RETRY_COUNT = 3
REQUEST_TIMEOUT = (10, 30)  # Render有超时限制

# ========== 日志设置 ==========
logger = logging.getLogger("YunYunProxyCloud")
logger.setLevel(logging.WARNING)  # 减少日志量以节省资源

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console_handler)

# 文件输出（可选，Render可能有写文件限制）
try:
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
except:
    logger.warning("无法创建日志文件，仅使用控制台日志")

# ========== 认证系统 ==========
auth = HTTPBasicAuth()
users = {}

# 初始化用户
if AUTH_PASSWORD:
    users[AUTH_USERNAME] = generate_password_hash(AUTH_PASSWORD)

@auth.verify_password
def verify_password(username, password):
    if not REQUIRE_AUTH:
        return True
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

def check_api_key_auth():
    """检查API密钥认证"""
    if not USE_API_KEY_AUTH or not API_KEY:
        return True
    
    provided_key = request.headers.get('X-API-Key')
    if provided_key and provided_key == API_KEY:
        return True
    return False

# ========== 数据存储辅助函数 ==========
def get_encrypt_key():
    if not CRYPTO_AVAILABLE or not ENCRYPT_ENABLED:
        return None
    
    # 优先从环境变量读取加密密钥
    env_key = os.environ.get("ENCRYPTION_KEY")
    if env_key:
        return env_key.encode()
    
    # 否则从文件读取或生成
    key_file = Path(ENCRYPT_KEY_FILE)
    if key_file.exists():
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        # 存储到文件（Render重启会丢失，但可以手动设置环境变量）
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
        except:
            pass
        return key

def encrypt_data(data):
    key = get_encrypt_key()
    if key is None:
        return data
    try:
        cipher = Fernet(key)
        return cipher.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"加密失败: {e}")
        return data

def decrypt_data(data):
    key = get_encrypt_key()
    if key is None:
        return data
    try:
        cipher = Fernet(key)
        return cipher.decrypt(data.encode()).decode()
    except:
        return data

# ========== 数据加载与保存 ==========
_MEM_CACHE = None

def load_data():
    """加载密钥数据"""
    global _MEM_CACHE
    if _MEM_CACHE is not None:
        return _MEM_CACHE
    
    if USE_ENV_STORAGE:
        # 从环境变量读取数据
        env_data = os.environ.get("KEYS_DATA")
        if env_data:
            try:
                data = json.loads(env_data)
                _MEM_CACHE = data
                return data
            except:
                pass
    
    # 从文件读取
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = f.read()
                if raw.startswith("enc:"):
                    decrypted = decrypt_data(raw[4:])
                    data = json.loads(decrypted)
                else:
                    data = json.loads(raw)
                
                # 初始化缺失字段
                if "keys" not in data:
                    data["keys"] = []
                if "active_key" not in data:
                    data["active_key"] = None
                
                # 兼容旧数据
                for k in data["keys"]:
                    if "fail_count" not in k:
                        k["fail_count"] = 0
                
                _MEM_CACHE = data
                return data
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
    
    _MEM_CACHE = {"keys": [], "active_key": None}
    return _MEM_CACHE

def save_data(data):
    """保存密钥数据"""
    global _MEM_CACHE
    
    # 按余额排序
    def get_balance_val(item):
        try:
            bal = item.get("balance", "0")
            if isinstance(bal, (int, float)):
                return bal
            if isinstance(bal, str):
                try:
                    return float(bal)
                except:
                    return float('inf')
            return float('inf')
        except:
            return float('inf')
    
    data["keys"] = sorted(data["keys"], key=get_balance_val)
    _MEM_CACHE = data
    
    # 序列化数据
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    # 加密存储
    if CRYPTO_AVAILABLE and ENCRYPT_ENABLED and get_encrypt_key():
        encrypted = "enc:" + encrypt_data(json_str)
        storage_str = encrypted
    else:
        storage_str = json_str
    
    # 存储到文件
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(storage_str)
    except Exception as e:
        logger.error(f"保存到文件失败: {e}")
    
    # 如果启用了环境变量存储，也可以更新环境变量（但需要重启才能生效）
    # 在Render中，建议通过UI界面设置环境变量

# ========== Flask 应用 ==========
app = Flask(__name__)

def check_auth():
    """统一的认证检查"""
    if not REQUIRE_AUTH:
        return True
    
    if USE_API_KEY_AUTH:
        return check_api_key_auth()
    else:
        # Basic Auth检查
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Basic "):
            return auth.get_auth() is not None
        # 没有认证头时，尝试其他方式（比如在浏览器中会弹出认证框）
        return request.authorization is not None

@app.route("/")
def index():
    """主页面 - 显示管理界面"""
    if not check_auth():
        return Response(
            "请输入用户名和密码登录",
            401,
            {"WWW-Authenticate": 'Basic realm="YunYun Proxy - 请登录"'}
        )
    
    # 简化的管理界面
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YunYun AI Proxy (云端版)</title>
        <style>
            body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .card { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
            .btn { background: #007bff; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🌸 YunYun AI 代理服务 (云端版)</h1>
        <div class="card">
            <h2>状态信息</h2>
            <p>版本: {{ version }}</p>
            <p>密钥数量: {{ key_count }}</p>
            <p>代理地址: <code>{{ proxy_url }}/v1/chat/completions</code></p>
            <p>管理API: <code>{{ base_url }}/api/data</code></p>
        </div>
        <div class="card">
            <h2>快速使用</h2>
            <h3>API代理端点:</h3>
            <pre>POST {{ proxy_url }}/v1/chat/completions</pre>
            <h3>请求头:</h3>
            <pre>Content-Type: application/json
{% if require_auth %}
{% if use_api_key_auth %}
X-API-Key: [你的API密钥]
{% else %}
Authorization: Basic [base64编码的用户名:密码]
{% endif %}
{% endif %}</pre>
            <h3>请求体:</h3>
            <pre>{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [{"role": "user", "content": "你好"}],
  "stream": false
}</pre>
        </div>
        <div class="card">
            <h2>管理功能</h2>
            <button class="btn" onclick="location.href='/api/data'">查看密钥列表</button>
            <button class="btn" onclick="showImport()">导入密钥</button>
        </div>
        <script>
            function showImport() {
                alert('请在终端中使用curl命令导入密钥:\\ncurl -X POST "{{ base_url }}/api/data" -H "Content-Type: application/json" -d \'{"keys":[{"key":"sk-xxx","balance":"未知","fail_count":0}],"active_key":"sk-xxx"}\'');
            }
        </script>
    </body>
    </html>
    """
    
    data = load_data()
    base_url = request.base_url.rstrip('/')
    
    return render_template_string(html_content, 
        version=VERSION,
        key_count=len(data.get("keys", [])),
        proxy_url=base_url,
        base_url=base_url,
        require_auth=REQUIRE_AUTH,
        use_api_key_auth=USE_API_KEY_AUTH
    )

@app.route("/api/data", methods=["GET", "POST"])
@auth.login_required
def manage_data():
    """管理密钥数据（需要认证）"""
    if request.method == "POST":
        data = request.json
        if "keys" not in data:
            data["keys"] = []
        if "active_key" not in data:
            data["active_key"] = None
        save_data(data)
        return jsonify({"status": "success", "data": load_data()})
    return jsonify(load_data())

@app.route("/api/check_balance", methods=["POST"])
@auth.login_required
def check_balance():
    """检查单个密钥余额"""
    key = request.json.get("key")
    if not key:
        return jsonify({"balance": "无效Key"}), 400
    try:
        resp = requests.get(
            f"{API_BASE}/user/info",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            balance = data.get("data", {}).get("totalBalance", "获取失败")
            if isinstance(balance, (int, float)):
                balance = f"{balance:.2f}"
            # 重置失败计数
            full_data = load_data()
            for k in full_data["keys"]:
                if k["key"] == key:
                    k["fail_count"] = 0
                    break
            save_data(full_data)
            return jsonify({"balance": balance})
        else:
            # 增加失败计数
            if resp.status_code in (401, 403):
                full_data = load_data()
                for k in full_data["keys"]:
                    if k["key"] == key:
                        k["fail_count"] = k.get("fail_count", 0) + 1
                        break
                save_data(full_data)
            return jsonify({"balance": "查询失败"})
    except Exception as e:
        return jsonify({"balance": "网络异常"})

@app.route("/api/export_backup", methods=["GET"])
@auth.login_required
def export_backup():
    """导出备份"""
    return jsonify(load_data())

@app.route("/api/import_backup", methods=["POST"])
@auth.login_required
def import_backup():
    """导入备份"""
    try:
        data = request.json
        save_data(data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/export_keys_text", methods=["GET"])
@auth.login_required
def export_keys_text():
    """导出所有Key的明文"""
    data = load_data()
    keys = [k["key"] for k in data.get("keys", [])]
    plain = "\n".join(keys)
    return Response(plain, mimetype="text/plain", headers={"Content-Disposition": "attachment;filename=keys.txt"})

@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查端点（不需要认证）"""
    return jsonify({
        "status": "healthy",
        "version": VERSION,
        "key_count": len(load_data().get("keys", [])),
        "encryption_enabled": ENCRYPT_ENABLED and CRYPTO_AVAILABLE
    })

@app.route("/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy(path):
    """代理请求到硅基流动API"""
    # 检查认证
    if not check_auth():
        return jsonify({"error": "认证失败"}), 401
    
    # 加载数据
    data = load_data()
    keys = data.get("keys", [])
    
    # 过滤掉失败次数过多的 Key
    valid_keys = [k for k in keys if k.get("fail_count", 0) < 3]
    if not valid_keys:
        return jsonify({"error": "未配置任何有效的 API Key"}), 400
    
    # 获取模型信息和流式请求标志
    model = "unknown"
    if request.is_json:
        json_data = request.get_json()
        model = json_data.get("model", "unknown")
    is_stream = request.is_json and json_data.get("stream", False)
    
    start_time = time.time()
    active_key_val = data.get("active_key")
    ordered_keys = []
    
    # 优先使用活跃密钥
    if active_key_val:
        for k in valid_keys:
            if k["key"] == active_key_val:
                ordered_keys.append(k)
                break
    # 添加其他密钥
    for k in valid_keys:
        if k["key"] != active_key_val:
            ordered_keys.append(k)
    
    # 构建请求头
    base_headers = {}
    for k, v in request.headers:
        if k.lower() not in ['host', 'authorization']:
            base_headers[k] = v
    
    last_error = None
    for attempt_idx, key_item in enumerate(ordered_keys[:RETRY_COUNT]):
        current_key = key_item["key"]
        headers = base_headers.copy()
        headers["Authorization"] = f"Bearer {current_key}"
        
        try:
            resp = requests.request(
                method=request.method,
                url=f"{API_BASE}/{path}",
                headers=headers,
                data=request.get_data(),
                stream=is_stream,
                timeout=REQUEST_TIMEOUT
            )
            elapsed = (time.time() - start_time) * 1000
            
            if resp.status_code in (401, 403, 429):
                # 增加失败计数
                for k in data["keys"]:
                    if k["key"] == current_key:
                        k["fail_count"] = k.get("fail_count", 0) + 1
                        break
                save_data(data)
                last_error = resp.status_code
                continue
            
            # 请求成功，重置失败计数
            for k in data["keys"]:
                if k["key"] == current_key:
                    k["fail_count"] = 0
                    break
            save_data(data)
            
            # 构建响应头
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            response_headers = [(name, value) for name, value in resp.raw.headers.items()
                                if name.lower() not in excluded_headers]
            
            if is_stream:
                return Response(resp.iter_content(chunk_size=1024), status=resp.status_code, headers=response_headers)
            else:
                return Response(resp.content, status=resp.status_code, headers=response_headers, content_type=resp.headers.get('content-type'))
        
        except requests.exceptions.Timeout:
            last_error = "timeout"
            # 超时增加失败计数
            for k in data["keys"]:
                if k["key"] == current_key:
                    k["fail_count"] = k.get("fail_count", 0) + 1
                    break
            save_data(data)
            continue
        except Exception as e:
            last_error = str(e)
            continue
    
    return jsonify({"error": f"所有可用Key均失败，最后错误: {last_error}"}), 500

def mask_key(key):
    """脱敏显示密钥"""
    if not key: return ""
    if len(key) <= 8: return "***"
    return key[:5] + "..." + key[-4:]

# ========== 启动应用 ==========
# 注意：这个文件现在是模块，通过app.py启动
# 请不要直接运行此文件
