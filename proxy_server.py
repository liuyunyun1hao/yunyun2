import os
import json
import sys
import subprocess
import signal
import time
from flask import Flask, request, jsonify, Response
import requests

app = Flask(__name__)
DATA_FILE = "keys_data.json"
PID_FILE = "server.pid"
API_BASE = "https://api.siliconflow.cn/v1"

# === 数据管理与路由逻辑 ===
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"keys": [], "active_key": None}

def save_data(data):
    def get_balance_val(item):
        try: return float(item.get("balance", 0))
        except: return float('inf')
    data["keys"] = sorted(data["keys"], key=get_balance_val)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route("/")
def index(): return HTML_CONTENT

@app.route("/api/data", methods=["GET", "POST"])
def manage_data():
    if request.method == "POST":
        save_data(request.json)
        return jsonify({"status": "success", "data": load_data()})
    return jsonify(load_data())

@app.route("/api/check_balance", methods=["POST"])
def check_balance():
    key = request.json.get("key")
    try:
        res = requests.get(f"{API_BASE}/user/info", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        res_data = res.json()
        if res.status_code == 200 and "data" in res_data:
            return jsonify({"balance": res_data["data"].get("totalBalance", "获取失败")})
    except Exception: pass
    return jsonify({"balance": "错误/网络异常"})

@app.route("/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy(path):
    data = load_data()
    active_key = data.get("active_key")
    if not active_key: return jsonify({"error": "未选择活动 Key"}), 400

    url = f"{API_BASE}/{path}"
    headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'authorization']}
    headers["Authorization"] = f"Bearer {active_key}"

    stream = request.json.get("stream", False) if request.is_json else False
    try:
        resp = requests.request(method=request.method, url=url, headers=headers, data=request.get_data(), stream=stream, timeout=60)
        excluded = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        resp_headers = [(n, v) for (n, v) in resp.raw.headers.items() if n.lower() not in excluded]
        return Response(resp.iter_content(chunk_size=1024), resp.status_code, resp_headers)
    except Exception as e:
        return jsonify({"error": f"代理请求失败: {str(e)}"}), 500

# === 前端页面 ===
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>YunYun API Proxy</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css" />
    <script src="https://unpkg.com/element-plus"></script>
    <style>
        :root { --ios-bg: #f2f2f7; --ios-card: #ffffff; --ios-blue: #007aff; --ios-text: #1c1c1e; --ios-subtext: #8e8e93; }
        body { font-family: -apple-system, sans-serif; background-color: var(--ios-bg); color: var(--ios-text); margin: 0; padding: 16px; }
        .app-container { max-width: 800px; margin: 0 auto; padding-bottom: 40px;}
        .segmented-control { display: flex; background: #e3e3e8; border-radius: 8px; padding: 2px; margin-bottom: 20px; }
        .segment { flex: 1; text-align: center; padding: 8px 0; font-size: 14px; font-weight: 500; cursor: pointer; border-radius: 6px; color: var(--ios-text); }
        .segment.active { background: var(--ios-card); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .ios-card { background: var(--ios-card); border-radius: 16px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 20px; }
        .card-title { font-size: 20px; font-weight: 600; margin: 0 0 16px 0; display: flex; justify-content: space-between; align-items: center;}
        .el-button { border-radius: 8px !important; font-weight: 500 !important; }
        .el-table { border-radius: 12px; overflow: hidden; border: 1px solid #e5e5ea; }
        .test-box { background: #f9f9f9; padding: 16px; border-radius: 12px; margin-top: 16px; border: 1px solid #e5e5ea;}
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
            <h2 class="card-title">🔑 批量导入</h2>
            <el-input type="textarea" v-model="batchKeys" placeholder="在此粘贴多个 Key，每行一个" :rows="3"></el-input>
            <div style="margin-top: 16px; display: flex; gap: 12px;">
                <el-button type="primary" @click="importKeys">解析导入</el-button>
                <el-button @click="checkAllBalances" :loading="checking">一键刷新余额并排序</el-button>
            </div>
        </div>
        <div class="ios-card">
            <h2 class="card-title">📱 本地代理状态 <el-button size="small" type="primary" plain @click="copyText('http://127.0.0.1:5000/v1')">复制代理地址</el-button></h2>
            <el-table :data="keys" style="width: 100%" empty-text="暂无 Key，请在上方导入">
                <el-table-column label="启用" width="70" align="center">
                    <template #default="scope">
                        <el-radio v-model="activeKey" :label="scope.row.key" @change="saveData"><span></span></el-radio>
                    </template>
                </el-table-column>
                <el-table-column label="API Key" min-width="160">
                    <template #default="scope">
                        <span style="font-family: monospace;">{{ maskKey(scope.row.key) }}</span>
                    </template>
                </el-table-column>
                <el-table-column prop="balance" label="余额" width="90" align="center"></el-table-column>
                <el-table-column label="操作" width="80" align="center">
                    <template #default="scope"><el-button size="small" type="danger" text @click="deleteKey(scope.$index)">删除</el-button></template>
                </el-table-column>
            </el-table>
        </div>
    </div>

    <div v-show="activeTab === 'test'" class="ios-card">
        <h2 class="card-title">⚡ 代理连通性测试</h2>
        <div v-if="!activeKey" style="color: #ff3b30; text-align: center;">⚠️ 请先在【控制台】勾选一个 Key</div>
        <div v-else class="test-box">
            <el-input type="textarea" v-model="testPrompt" placeholder="输入测试内容" :rows="3"></el-input>
            <div style="margin-top: 12px; display: flex; gap: 10px;">
                <el-button type="primary" @click="sendTest" :loading="isTesting">发送测试</el-button>
                <el-button @click="sendTest" :loading="isTesting">重回</el-button>
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
            const keys = ref([]), activeKey = ref(null), batchKeys = ref(''), checking = ref(false);
            const testPrompt = ref('讲个冷笑话。'), testResult = ref(''), isTesting = ref(false);

            const loadData = async () => { const res = await fetch('/api/data'); const data = await res.json(); keys.value = data.keys || []; activeKey.value = data.active_key; };
            const saveData = async () => { const res = await fetch('/api/data', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ keys: keys.value, active_key: activeKey.value }) }); const result = await res.json(); keys.value = result.data.keys; };
            const maskKey = (key) => key ? key.substring(0, 6) + '...' + key.substring(key.length - 4) : '';
            const importKeys = async () => {
                const newKeys = batchKeys.value.split('\\n').map(k => k.trim()).filter(k => k.startsWith('sk-'));
                if (newKeys.length === 0) return ElementPlus.ElMessage.warning('未检测到有效 Key');
                newKeys.forEach(k => { if (!keys.value.some(exist => exist.key === k)) keys.value.push({ key: k, balance: '未知' }); });
                batchKeys.value = ''; await saveData(); ElementPlus.ElMessage.success(`导入完成`);
            };
            const deleteKey = async (index) => { if (keys.value[index].key === activeKey.value) activeKey.value = null; keys.value.splice(index, 1); await saveData(); };
            const checkAllBalances = async () => {
                checking.value = true;
                for (let i = 0; i < keys.value.length; i++) {
                    keys.value[i].balance = '...';
                    try { const res = await fetch('/api/check_balance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: keys.value[i].key }) }); const data = await res.json(); keys.value[i].balance = data.balance; } catch (e) { keys.value[i].balance = '超时'; }
                }
                await saveData(); checking.value = false; ElementPlus.ElMessage.success('刷新并排序完成');
            };
            const copyText = (text) => { navigator.clipboard.writeText(text).then(() => ElementPlus.ElMessage.success('已复制')).catch(() => ElementPlus.ElMessage.error('复制失败')); };
            const sendTest = async () => {
                if (!activeKey.value || !testPrompt.value.trim()) return;
                isTesting.value = true; testResult.value = '请求发送中...';
                try {
                    const response = await fetch('/v1/chat/completions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: "Qwen/Qwen2.5-7B-Instruct", messages: [{ role: "user", content: testPrompt.value }] }) });
                    const data = await response.json();
                    testResult.value = data.choices ? data.choices[0].message.content : `错误: ${JSON.stringify(data)}`;
                } catch (error) { testResult.value = `请求失败: ${error.message}`; } finally { isTesting.value = false; }
            };
            onMounted(() => loadData());
            return { activeTab, keys, activeKey, batchKeys, checking, testPrompt, testResult, isTesting, importKeys, checkAllBalances, deleteKey, maskKey, saveData, copyText, sendTest };
        }
    }).use(ElementPlus).mount('#app');
</script>
</body>
</html>
"""

# === 核心终端数字交互菜单 ===
def check_status():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0) # 测试进程是否存活
            return True
        except (OSError, ValueError):
            os.remove(PID_FILE) # 进程已死，清理废弃的 pid 文件
    return False

if __name__ == "__main__":
    # 如果检测到内部参数启动，说明这是负责运行网页的子进程
    if len(sys.argv) > 1 and sys.argv[1] == "run_app":
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR) # 屏蔽满屏的英文请求日志
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
        sys.exit(0)

    # ============ 终端交互界面 ============
    while True:
        os.system("clear") # 刷新清空屏幕内容
        print("\n==================================")
        print(" 🌟 YunYun API Proxy 快捷控制台")
        print("==================================")
        
        is_running = check_status()
        status_text = "🟢 运行中 (http://127.0.0.1:5000)" if is_running else "🔴 已停止"
        
        print(f" 当前状态: {status_text}")
        print("----------------------------------")
        print("  1. 启动代理服务")
        print("  2. 停止代理服务")
        print("  3. 从 GitHub 更新代码")
        print("  0. 退出控制台 (不影响后台运行)")
        print("==================================")
        
        choice = input(" 请输入数字并回车: ").strip()

        if choice == "1":
            if is_running:
                print("\n⚠️ 服务已经在运行中，无需重复启动。")
            else:
                print("\n🚀 正在后台启动服务...")
                # 核心：派生子进程跑服务，解放当前控制台
                p = subprocess.Popen([sys.executable, __file__, "run_app"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with open(PID_FILE, "w") as f:
                    f.write(str(p.pid))
                time.sleep(1.5)
                print("✅ 启动成功！你可以去手机浏览器访问了。")
            input("\n👉 按回车键返回主菜单...")

        elif choice == "2":
            if is_running:
                print("\n🛑 正在关闭服务...")
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                try:
                    os.kill(pid, signal.SIGTERM) # 杀掉后台服务进程
                except OSError:
                    pass
                os.remove(PID_FILE)
                print("✅ 代理服务已成功停止。")
            else:
                print("\n⚠️ 服务本来就是停止状态。")
            input("\n👉 按回车键返回主菜单...")

        elif choice == "3":
            print("\n🔄 正在从 GitHub 同步你的最新代码...\n")
            os.system("git pull")
            print("\n✅ 更新完毕！(如果想应用新代码，请先按 2 停止，再按 1 启动)")
            input("\n👉 按回车键返回主菜单...")

        elif choice == "0":
            print("\n👋 拜拜！")
            if check_status():
                print("💡 提示：代理服务依然在【后台】默默运行，供你的 AI 软件调用。")
                print("如果将来你想彻底关闭它，只需重新运行此脚本，然后按 2 即可。")
            sys.exit(0)
            
        else:
            print("\n❌ 输入无效，请输入 0, 1, 2, 或 3。")
            time.sleep(1)
