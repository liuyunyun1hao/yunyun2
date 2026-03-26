import os
import json
import sys
import subprocess
import signal
import time
import logging
import socket
from flask import Flask, request, jsonify, Response
import requests

# === 配置 ===
VERSION = "3.7"                     # 当前版本号
DATA_FILE = "keys_data.json"        # 存储API密钥的文件
PID_FILE = "server.pid"             # 代理进程PID文件
ST_PID_FILE = "st_server.pid"       # 酒馆进程PID文件
API_BASE = "https://api.siliconflow.cn/v1"
ST_DIR = os.path.expanduser("~/SillyTavern")
PORT = 5000                         # 代理服务端口
ST_PORT = 8000                      # 酒馆默认端口

# 日志配置
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# === 辅助函数 ===
def load_data():
    """加载密钥数据，确保结构完整"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "keys" not in data:
                    data["keys"] = []
                if "active_key" not in data:
                    data["active_key"] = None
                return data
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
    return {"keys": [], "active_key": None}

def save_data(data):
    """保存数据，按余额排序（数值小的优先）"""
    def get_balance_val(item):
        try:
            bal = item.get("balance", "0")
            # 处理可能的字符串（如 "1.23" 或 "未知"）
            if isinstance(bal, (int, float)):
                return bal
            if isinstance(bal, str):
                # 尝试转换为浮点数
                try:
                    return float(bal)
                except ValueError:
                    return float('inf')
            return float('inf')
        except:
            return float('inf')

    data["keys"] = sorted(data["keys"], key=get_balance_val)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return False   # 端口空闲
    except socket.error:
        return True    # 端口被占用

def kill_process(pid_file):
    """安全终止进程并删除PID文件"""
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
                # 如果进程还存在，强制杀死
                try:
                    os.kill(pid, 0)
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
        except Exception as e:
            logger.warning(f"终止进程失败: {e}")
        finally:
            try:
                os.remove(pid_file)
            except:
                pass

def is_running(pid_file):
    """检查进程是否存活"""
    if not os.path.exists(pid_file):
        return False
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
    except:
        # PID文件无效，删除它
        try:
            os.remove(pid_file)
        except:
            pass
        return False

# === 版本检测 ===
def check_proxy_update():
    try:
        url = "https://raw.githubusercontent.com/liuyunyun1hao/yunyun2/main/proxy_server.py"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            # 简单查找版本号
            if f'VERSION = "{VERSION}"' not in res.text:
                return "✨(有新版本)"
            else:
                return "✅(最新)"
        return "⚠️(检测失败)"
    except:
        return "⚠️(网络异常)"

def check_st_versions():
    local_ver = "未安装"
    if os.path.exists(os.path.join(ST_DIR, "package.json")):
        try:
            with open(os.path.join(ST_DIR, "package.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                local_ver = data.get("version", "未知")
        except:
            pass

    remote_ver = "获取中"
    try:
        url = "https://raw.githubusercontent.com/SillyTavern/SillyTavern/release/package.json"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            remote_ver = res.json().get("version", "未知")
    except:
        remote_ver = "超时"

    return local_ver, remote_ver

# === API 路由 ===
@app.route("/")
def index():
    return HTML_CONTENT

@app.route("/api/data", methods=["GET", "POST"])
def manage_data():
    if request.method == "POST":
        data = request.json
        # 确保数据结构正确
        if "keys" not in data:
            data["keys"] = []
        if "active_key" not in data:
            data["active_key"] = None
        save_data(data)
        return jsonify({"status": "success", "data": load_data()})
    return jsonify(load_data())

@app.route("/api/check_balance", methods=["POST"])
def check_balance():
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
            # 确保返回字符串便于显示
            if isinstance(balance, (int, float)):
                balance = f"{balance:.2f}"
            return jsonify({"balance": balance})
        else:
            logger.warning(f"余额查询失败: {resp.status_code} - {resp.text}")
            return jsonify({"balance": "查询失败"})
    except Exception as e:
        logger.error(f"余额检查异常: {e}")
        return jsonify({"balance": "网络异常"})

@app.route("/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy(path):
    data = load_data()
    active_key = data.get("active_key")
    if not active_key:
        return jsonify({"error": "未选择活动 Key"}), 400

    # 构建请求头，过滤掉 host 和 authorization
    headers = {}
    for k, v in request.headers:
        if k.lower() not in ['host', 'authorization']:
            headers[k] = v
    headers["Authorization"] = f"Bearer {active_key}"

    # 判断是否为流式请求
    is_stream = False
    if request.is_json:
        json_data = request.get_json()
        is_stream = json_data.get("stream", False)

    try:
        # 转发请求
        resp = requests.request(
            method=request.method,
            url=f"{API_BASE}/{path}",
            headers=headers,
            data=request.get_data(),
            stream=is_stream,
            timeout=(5, 60)  # (连接超时, 读取超时)
        )
        # 构造响应头，排除某些自动处理的头
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for name, value in resp.raw.headers.items()
                            if name.lower() not in excluded_headers]

        # 流式响应直接使用生成器
        if is_stream:
            return Response(resp.iter_content(chunk_size=1024),
                            status=resp.status_code,
                            headers=response_headers)
        else:
            # 非流式直接返回内容
            return Response(resp.content,
                            status=resp.status_code,
                            headers=response_headers,
                            content_type=resp.headers.get('content-type'))

    except requests.exceptions.Timeout:
        logger.error("代理请求超时")
        return jsonify({"error": "请求上游超时"}), 504
    except Exception as e:
        logger.error(f"代理错误: {e}")
        return jsonify({"error": f"代理失败: {str(e)}"}), 500

# === 前端 HTML（改进版） ===
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>YunYun Proxy</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css" />
    <script src="https://unpkg.com/element-plus"></script>
    <style>
        :root { --theme-pink: #ff8fa3; --theme-pink-hover: #ff9fb1; --glass-bg: rgba(255, 255, 255, 0.65); --glass-border: rgba(255, 255, 255, 0.5); --text-main: #4a3b3e; --text-sub: #9c898c; }
        body { font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #fdf4f6 0%, #fbe1e6 100%); background-attachment: fixed; color: var(--text-main); margin: 0; padding: calc(env(safe-area-inset-top) + 16px) 16px calc(env(safe-area-inset-bottom) + 40px) 16px; }
        .app-container { max-width: 800px; margin: 0 auto; }
        .segmented-control { display: flex; background: rgba(255, 255, 255, 0.4); border: 1px solid var(--glass-border); backdrop-filter: blur(12px); border-radius: 14px; padding: 4px; margin-bottom: 24px; }
        .segment { flex: 1; text-align: center; padding: 10px 0; font-size: 14px; font-weight: 600; cursor: pointer; border-radius: 10px; color: var(--text-sub); transition: all 0.3s ease; }
        .segment.active { background: rgba(255, 255, 255, 0.9); color: var(--theme-pink); box-shadow: 0 2px 10px rgba(255, 143, 163, 0.15); }
        .ios-card { background: var(--glass-bg); backdrop-filter: blur(20px); border: 1px solid var(--glass-border); border-radius: 24px; padding: 24px; box-shadow: 0 10px 40px rgba(255, 143, 163, 0.1); margin-bottom: 24px; }
        .card-title { font-size: 20px; font-weight: 700; margin: 0 0 20px 0; display: flex; justify-content: space-between; align-items: center;}
        .el-button { border-radius: 12px !important; font-weight: 600 !important; border: none !important;}
        .el-button--primary { background-color: var(--theme-pink) !important; color: white !important; box-shadow: 0 4px 12px rgba(255, 143, 163, 0.3) !important; }
        .el-button--primary:active { background-color: var(--theme-pink-hover) !important; transform: scale(0.98); }
        .el-input__wrapper, .el-textarea__inner { border-radius: 14px !important; background: rgba(255, 255, 255, 0.7) !important; box-shadow: 0 0 0 1px rgba(255, 143, 163, 0.2) inset !important; }
        .el-input__wrapper.is-focus, .el-textarea__inner:focus { box-shadow: 0 0 0 2px var(--theme-pink) inset !important; background: #fff !important; }
        .el-table { border-radius: 16px; overflow: hidden; background: transparent !important; }
        .el-table tr, .el-table th.el-table__cell { background-color: rgba(255, 255, 255, 0.5) !important; color: var(--text-main); font-weight: 600; border-bottom: 1px solid rgba(255, 143, 163, 0.1) !important;}
        .el-table td.el-table__cell { border-bottom: 1px solid rgba(255, 143, 163, 0.1) !important; background: transparent !important;}
        .el-table--enable-row-hover .el-table__body tr:hover>td.el-table__cell { background-color: rgba(255, 255, 255, 0.8) !important; }
        .el-radio__input.is-checked .el-radio__inner { border-color: var(--theme-pink) !important; background: var(--theme-pink) !important; }
        .el-radio__input.is-checked+.el-radio__label { color: var(--theme-pink) !important; }
        .test-box { background: rgba(255, 255, 255, 0.4); padding: 16px; border-radius: 16px; margin-top: 16px; border: 1px solid var(--glass-border);}
        .add-key-area { margin-top: 20px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
        .add-key-area .el-input { flex: 1; min-width: 200px; }
    </style>
</head>
<body>
<div id="app" class="app-container">
    <div class="segmented-control">
        <div class="segment" :class="{active: activeTab === 'console'}" @click="activeTab = 'console'">控制台</div>
        <div class="segment" :class="{active: activeTab === 'test'}" @click="activeTab = 'test'">连接测试</div>
    </div>
    <div v-show="activeTab === 'console'">
        <div class="ios-card">
            <h2 class="card-title">🌸 批量导入</h2>
            <el-input type="textarea" v-model="batchKeys" placeholder="在此粘贴 Key，每行一个" :rows="3"></el-input>
            <div style="margin-top: 16px; display: flex; gap: 12px;">
                <el-button type="primary" @click="importKeys">解析导入</el-button>
                <el-button @click="checkAllBalances" :loading="checking" style="color: var(--theme-pink); background: rgba(255, 255, 255, 0.8);">刷新余额</el-button>
            </div>
            <div class="add-key-area">
                <el-input v-model="singleKey" placeholder="手动输入单个 Key (sk-开头)" @keyup.enter="addSingleKey"></el-input>
                <el-button type="primary" @click="addSingleKey">添加</el-button>
            </div>
        </div>
        <div class="ios-card">
            <h2 class="card-title">✨ 代理状态 <el-button size="small" type="primary" @click="copyText('http://127.0.0.1:5000/v1')" style="box-shadow: none !important;">复制地址</el-button></h2>
            <el-table :data="keys" style="width: 100%" empty-text="暂无数据">
                <el-table-column label="启用" width="60" align="center"><template #default="scope"><el-radio v-model="activeKey" :label="scope.row.key" @change="saveData"><span></span></el-radio></template></el-table-column>
                <el-table-column label="API Key" min-width="150"><template #default="scope"><span style="font-family: monospace; color: var(--text-sub);">{{ maskKey(scope.row.key) }}</span></template></el-table-column>
                <el-table-column prop="balance" label="余额" width="100" align="center"></el-table-column>
                <el-table-column label="操作" width="70" align="center"><template #default="scope"><el-button size="small" type="danger" text @click="deleteKey(scope.$index)">删除</el-button></template></el-table-column>
            </el-table>
        </div>
    </div>
    <div v-show="activeTab === 'test'" class="ios-card">
        <h2 class="card-title">⚡ 连通性测试</h2>
        <div v-if="!activeKey" style="color: #ff4d4f; text-align: center; font-weight: bold;">⚠️ 请先在【控制台】勾选一个 Key</div>
        <div v-else class="test-box">
            <el-input type="textarea" v-model="testPrompt" placeholder="输入测试内容..." :rows="3"></el-input>
            <div style="margin-top: 16px; display: flex; gap: 10px;">
                <el-button type="primary" @click="sendTest" :loading="isTesting">发送请求</el-button>
                <el-button @click="testPrompt = ''; testResult = ''" style="background: rgba(255,255,255,0.8); color: var(--text-sub);">清空</el-button>
            </div>
            <el-input v-if="testResult" type="textarea" v-model="testResult" :rows="6" readonly style="margin-top: 16px;"></el-input>
        </div>
    </div>
</div>
<script>
    const { createApp, ref, onMounted } = Vue;
    createApp({
        setup() {
            const activeTab = ref('console');
            const keys = ref([]);
            const activeKey = ref(null);
            const batchKeys = ref('');
            const singleKey = ref('');
            const checking = ref(false);
            const testPrompt = ref('讲个冷笑话。');
            const testResult = ref('');
            const isTesting = ref(false);

            const loadData = async () => {
                const res = await fetch('/api/data');
                const data = await res.json();
                keys.value = data.keys || [];
                activeKey.value = data.active_key;
            };
            const saveData = async () => {
                const res = await fetch('/api/data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keys: keys.value, active_key: activeKey.value })
                });
                const result = await res.json();
                keys.value = result.data.keys;
            };
            const maskKey = (key) => {
                if (!key) return '';
                if (key.length <= 8) return '***';
                return key.substring(0, 5) + '...' + key.substring(key.length - 4);
            };
            const importKeys = async () => {
                const lines = batchKeys.value.split('\\n');
                const newKeys = [];
                for (let line of lines) {
                    line = line.trim();
                    if (line.startsWith('sk-') && !keys.value.some(k => k.key === line)) {
                        newKeys.push({ key: line, balance: '未知' });
                    }
                }
                if (newKeys.length === 0) {
                    ElementPlus.ElMessage.warning('没有有效的 Key（需以 sk- 开头）');
                    return;
                }
                keys.value.push(...newKeys);
                batchKeys.value = '';
                await saveData();
                ElementPlus.ElMessage.success(`成功导入 ${newKeys.length} 个 Key`);
            };
            const addSingleKey = async () => {
                let key = singleKey.value.trim();
                if (!key.startsWith('sk-')) {
                    ElementPlus.ElMessage.warning('Key 必须以 sk- 开头');
                    return;
                }
                if (keys.value.some(k => k.key === key)) {
                    ElementPlus.ElMessage.warning('Key 已存在');
                    return;
                }
                keys.value.push({ key, balance: '未知' });
                singleKey.value = '';
                await saveData();
                ElementPlus.ElMessage.success('添加成功');
            };
            const deleteKey = async (index) => {
                if (keys.value[index].key === activeKey.value) {
                    activeKey.value = null;
                }
                keys.value.splice(index, 1);
                await saveData();
            };
            const checkAllBalances = async () => {
                checking.value = true;
                for (let i = 0; i < keys.value.length; i++) {
                    keys.value[i].balance = '...';
                    try {
                        const res = await fetch('/api/check_balance', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ key: keys.value[i].key })
                        });
                        const data = await res.json();
                        keys.value[i].balance = data.balance;
                    } catch (e) {
                        keys.value[i].balance = '请求失败';
                    }
                    // 每检查完一个就保存一次，避免中断丢失
                    await saveData();
                }
                checking.value = false;
                ElementPlus.ElMessage.success('余额刷新完成');
            };
            const copyText = (text) => {
                navigator.clipboard.writeText(text).then(() => {
                    ElementPlus.ElMessage.success('已复制');
                }).catch(() => {
                    ElementPlus.ElMessage.error('复制失败');
                });
            };
            const sendTest = async () => {
                if (!activeKey.value) {
                    ElementPlus.ElMessage.warning('请先选择一个活动 Key');
                    return;
                }
                if (!testPrompt.value.trim()) {
                    ElementPlus.ElMessage.warning('请输入测试内容');
                    return;
                }
                isTesting.value = true;
                testResult.value = '请求发送中...';
                try {
                    const response = await fetch('/v1/chat/completions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            model: "Qwen/Qwen2.5-7B-Instruct",
                            messages: [{ role: "user", content: testPrompt.value }],
                            stream: false
                        })
                    });
                    const data = await response.json();
                    if (response.ok && data.choices && data.choices.length) {
                        testResult.value = data.choices[0].message.content;
                    } else {
                        testResult.value = `错误: ${JSON.stringify(data)}`;
                    }
                } catch (error) {
                    testResult.value = `请求失败: ${error.message}`;
                } finally {
                    isTesting.value = false;
                }
            };

            onMounted(loadData);
            return {
                activeTab,
                keys,
                activeKey,
                batchKeys,
                singleKey,
                checking,
                testPrompt,
                testResult,
                isTesting,
                importKeys,
                addSingleKey,
                checkAllBalances,
                deleteKey,
                maskKey,
                saveData,
                copyText,
                sendTest
            };
        }
    }).use(ElementPlus).mount('#app');
</script>
</body>
</html>
"""

# === 控制台菜单（改进版） ===
def show_menu():
    proxy_update = check_proxy_update()
    st_local, st_remote = check_st_versions()
    proxy_running = is_running(PID_FILE)
    st_running = is_running(ST_PID_FILE)

    os.system("clear")
    print("\n╭──────────────────────────────╮")
    print(f"  🌸 YunYun AI 控制台 [v{VERSION}]")
    print("╰──────────────────────────────╯")
    print("\n🔑 【API 本地代理】")
    print(f" 状态: {'🟢 运行中' if proxy_running else '🔴 已停止'}  {proxy_update}")
    print(" 🔗 网页: http://127.0.0.1:5000")
    print("\n🍻 【傻酒馆 SillyTavern】")
    print(f" 状态: {'🟢 运行中' if st_running else '🔴 已停止'}")
    print(f" 版本: {st_local}(本地) | {st_remote}(最新)")
    print(" 🔗 网页: http://127.0.0.1:8000")
    print("\n" + "─" * 32)
    print("  1. 启动代理    2. 停止代理")
    print("  3. 启动酒馆    4. 停止酒馆")
    print("  5. 一键更新    6. 自启教程")
    print("  0. 退出控制台")
    print("─" * 32)

def start_proxy():
    if is_running(PID_FILE):
        print("\n⚠️ 代理已在运行！")
        return
    if check_port(PORT):
        print(f"\n⚠️ 端口 {PORT} 已被占用，可能已有服务运行。")
        return
    try:
        p = subprocess.Popen(
            [sys.executable, __file__, "run_app"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        with open(PID_FILE, "w") as f:
            f.write(str(p.pid))
        # 等待服务启动（最多5秒）
        for _ in range(10):
            if not check_port(PORT):
                print("\n✅ 代理启动成功！")
                return
            time.sleep(0.5)
        print("\n⚠️ 启动可能失败，请检查日志。")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

def stop_proxy():
    kill_process(PID_FILE)
    print("\n✅ 代理已停止。")

def start_sillytavern():
    if is_running(ST_PID_FILE):
        print("\n⚠️ 傻酒馆已在运行！")
        return
    if check_port(ST_PORT):
        print(f"\n⚠️ 端口 {ST_PORT} 已被占用，可能已有服务运行。")
        return
    if not os.path.exists(ST_DIR):
        print("\n📥 首次使用，正在部署傻酒馆...")
        print("→ 安装必要工具...")
        if os.system("pkg install nodejs git -y") != 0:
            print("❌ 安装工具失败，请确保网络正常并重试。")
            return
        print("\n→ 克隆代码仓库...")
        if os.system(f"git clone https://github.com/SillyTavern/SillyTavern.git {ST_DIR}") != 0:
            print("❌ 克隆失败，请检查网络（可能需要全局代理）。")
            return
        print("\n→ 安装依赖包...")
        if os.system(f"cd {ST_DIR} && npm install") != 0:
            print("❌ 依赖安装失败，请检查网络。")
            return
        print("✅ 部署完成！")
    else:
        # 如果已存在，尝试更新依赖
        print("\n⏳ 检查依赖更新...")
        os.system(f"cd {ST_DIR} && npm install 2>/dev/null")

    print("\n🚀 启动傻酒馆中...")
    try:
        p = subprocess.Popen(
            ["node", "server.js"],
            cwd=ST_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        with open(ST_PID_FILE, "w") as f:
            f.write(str(p.pid))
        # 等待启动
        for _ in range(10):
            if not check_port(ST_PORT):
                print("✅ 傻酒馆启动成功！")
                return
            time.sleep(0.5)
        print("⚠️ 启动可能失败，请手动检查。")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")

def stop_sillytavern():
    kill_process(ST_PID_FILE)
    print("\n✅ 傻酒馆已停止。")

def update_all():
    print("\n🔄 正在拉取代码更新...")
    os.system("git pull")
    if os.path.exists(ST_DIR):
        print("→ 更新酒馆...")
        os.system(f"cd {ST_DIR} && git pull && npm install")
    print("\n✅ 更新完毕！(重启服务生效)")
    input("\n👉 按回车继续...")

def show_autostart_help():
    print("\n" + "─" * 32)
    print(" 📖 【Termux 开机自启教程】")
    print("─" * 32)
    print(" Termux 默认是 Login Shell，请务必使用 .bash_profile")
    print("\n 👉 请复制以下整段代码（直接长按选中），")
    print(" 在主菜单按 0 退出后，粘贴并回车：\n")
    print('echo \'if [ -z "$TMUX" ]; then cd ~/yunyun2 && python proxy_server.py; fi\' >> ~/.bash_profile')
    print("source ~/.bash_profile")
    print("\n ✅ 完成后，下次打开 Termux 就会自动弹出了！")
    input("\n👉 按回车返回...")

# === 主程序入口 ===
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_app":
        # 作为后台服务运行
        app.run(host="0.0.0.0", port=PORT, use_reloader=False, debug=False)
        sys.exit(0)

    # 控制台菜单循环
    while True:
        show_menu()
        choice = input(" 请输入数字指令: ").strip()
        if choice == "1":
            start_proxy()
        elif choice == "2":
            stop_proxy()
        elif choice == "3":
            start_sillytavern()
        elif choice == "4":
            stop_sillytavern()
        elif choice == "5":
            update_all()
        elif choice == "6":
            show_autostart_help()
        elif choice == "0":
            os.system("clear")
            sys.exit(0)
        else:
            print("\n⚠️ 无效选项，请重试。")
        if choice not in ["5", "6"]:  # 更新和教程已自带等待
            input("\n👉 按回车返回...")