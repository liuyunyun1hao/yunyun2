import os
import json
import sys
import subprocess
import signal
import time
from flask import Flask, request, jsonify, Response
import requests

# === 当前本地版本号 ===
VERSION = "3.3"

app = Flask(__name__)
DATA_FILE = "keys_data.json"
PID_FILE = "server.pid"
ST_PID_FILE = "st_server.pid"
API_BASE = "https://api.siliconflow.cn/v1"
ST_DIR = os.path.expanduser("~/SillyTavern")

# === 自动版本检测 ===
def check_proxy_update():
    try:
        url = "https://raw.githubusercontent.com/liuyunyun1hao/yunyun2/main/proxy_server.py"
        res = requests.get(url, timeout=2)
        if res.status_code == 200 and f'VERSION = "{VERSION}"' not in res.text:
            return "✨ 发现新版"
        return "✅ 已是最新"
    except: return "⚠️ 检测失败"

def check_st_versions():
    local_ver = "未安装"
    if os.path.exists(os.path.join(ST_DIR, "package.json")):
        try:
            with open(os.path.join(ST_DIR, "package.json"), "r", encoding="utf-8") as f:
                local_ver = json.load(f).get("version", "未知")
        except: pass

    remote_ver = "获取中..."
    try:
        url = "https://raw.githubusercontent.com/SillyTavern/SillyTavern/release/package.json"
        res = requests.get(url, timeout=3)
        if res.status_code == 200: remote_ver = res.json().get("version", "未知")
    except: remote_ver = "超时"
    
    status_msg = "✨ 发现更新" if (local_ver != "未安装" and local_ver != remote_ver and remote_ver != "超时") else "✅ 最新版"
    return local_ver, remote_ver, status_msg

# === 数据管理与路由 ===
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
        if res.status_code == 200 and "data" in res.json():
            return jsonify({"balance": res.json()["data"].get("totalBalance", "获取失败")})
    except: pass
    return jsonify({"balance": "网络异常"})

@app.route("/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy(path):
    data = load_data()
    active_key = data.get("active_key")
    if not active_key: return jsonify({"error": "未选择活动 Key"}), 400

    headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'authorization']}
    headers["Authorization"] = f"Bearer {active_key}"
    stream = request.json.get("stream", False) if request.is_json else False
    
    try:
        resp = requests.request(method=request.method, url=f"{API_BASE}/{path}", headers=headers, data=request.get_data(), stream=stream, timeout=60)
        resp_headers = [(n, v) for (n, v) in resp.raw.headers.items() if n.lower() not in ['content-encoding', 'content-length', 'transfer-encoding', 'connection']]
        return Response(resp.iter_content(chunk_size=1024), resp.status_code, resp_headers)
    except Exception as e:
        return jsonify({"error": f"代理失败: {str(e)}"}), 500

# === 前端 UI ===
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
        </div>
        <div class="ios-card">
            <h2 class="card-title">✨ 代理状态 <el-button size="small" type="primary" @click="copyText('http://127.0.0.1:5000/v1')" style="box-shadow: none !important;">复制地址</el-button></h2>
            <el-table :data="keys" style="width: 100%" empty-text="暂无数据">
                <el-table-column label="启用" width="60" align="center"><template #default="scope"><el-radio v-model="activeKey" :label="scope.row.key" @change="saveData"><span></span></el-radio></template></el-table-column>
                <el-table-column label="API Key" min-width="150"><template #default="scope"><span style="font-family: monospace; color: var(--text-sub);">{{ maskKey(scope.row.key) }}</span></template></el-table-column>
                <el-table-column prop="balance" label="余额" width="80" align="center"></el-table-column>
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
            const activeTab = ref('console'); const keys = ref([]), activeKey = ref(null), batchKeys = ref(''), checking = ref(false);
            const testPrompt = ref('讲个冷笑话。'), testResult = ref(''), isTesting = ref(false);
            const loadData = async () => { const res = await fetch('/api/data'); const data = await res.json(); keys.value = data.keys || []; activeKey.value = data.active_key; };
            const saveData = async () => { const res = await fetch('/api/data', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ keys: keys.value, active_key: activeKey.value }) }); const result = await res.json(); keys.value = result.data.keys; };
            const maskKey = (key) => key ? key.substring(0, 5) + '...' + key.substring(key.length - 4) : '';
            const importKeys = async () => {
                const newKeys = batchKeys.value.split('\\n').map(k => k.trim()).filter(k => k.startsWith('sk-'));
                if (newKeys.length === 0) return ElementPlus.ElMessage.warning('无效的 Key');
                newKeys.forEach(k => { if (!keys.value.some(exist => exist.key === k)) keys.value.push({ key: k, balance: '未知' }); });
                batchKeys.value = ''; await saveData(); ElementPlus.ElMessage.success('导入完成');
            };
            const deleteKey = async (index) => { if (keys.value[index].key === activeKey.value) activeKey.value = null; keys.value.splice(index, 1); await saveData(); };
            const checkAllBalances = async () => { checking.value = true; for (let i = 0; i < keys.value.length; i++) { keys.value[i].balance = '...'; try { const res = await fetch('/api/check_balance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: keys.value[i].key }) }); const data = await res.json(); keys.value[i].balance = data.balance; } catch (e) { keys.value[i].balance = '超时'; } } await saveData(); checking.value = false; ElementPlus.ElMessage.success('排序完成'); };
            const copyText = (text) => { navigator.clipboard.writeText(text).then(() => ElementPlus.ElMessage.success('已复制')).catch(() => ElementPlus.ElMessage.error('复制失败')); };
            const sendTest = async () => { if (!activeKey.value || !testPrompt.value.trim()) return; isTesting.value = true; testResult.value = '请求发送中...'; try { const response = await fetch('/v1/chat/completions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: "Qwen/Qwen2.5-7B-Instruct", messages: [{ role: "user", content: testPrompt.value }] }) }); const data = await response.json(); testResult.value = data.choices ? data.choices[0].message.content : `错误: ${JSON.stringify(data)}`; } catch (error) { testResult.value = `失败: ${error.message}`; } finally { isTesting.value = false; } };
            onMounted(() => loadData());
            return { activeTab, keys, activeKey, batchKeys, checking, testPrompt, testResult, isTesting, importKeys, checkAllBalances, deleteKey, maskKey, saveData, copyText, sendTest };
        }
    }).use(ElementPlus).mount('#app');
</script>
</body>
</html>
"""

# === 终端进程控制模块 ===
def check_status(pid_path):
    if os.path.exists(pid_path):
        try:
            with open(pid_path, "r") as f: os.kill(int(f.read().strip()), 0)
            return True
        except: os.remove(pid_path)
    return False

def kill_process(pid_path):
    if os.path.exists(pid_path):
        with open(pid_path, "r") as f:
            try: os.kill(int(f.read().strip()), signal.SIGTERM)
            except: pass
        os.remove(pid_path)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_app":
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
        sys.exit(0)

    print("\n🔍 正在检测代码版本，请稍候...")
    proxy_update_msg = check_proxy_update()
    st_local, st_remote, st_status_msg = check_st_versions()

    while True:
        os.system("clear")
        print("\n" + "="*38)
        print(" 🌸 YunYun AI 聚合控制台 v" + VERSION)
        print("="*38)
        
        proxy_running = check_status(PID_FILE)
        st_running = check_status(ST_PID_FILE)
        
        print(f" [API代理] 状态: {'🟢 运行中 (5000)' if proxy_running else '🔴 已停止'} | {proxy_update_msg}")
        print(f" [傻酒馆]  状态: {'🟢 运行中 (8000)' if st_running else '🔴 已停止'}")
        print(f" [傻酒馆]  版本: 本地 {st_local} | 最新 {st_remote} ({st_status_msg})")
        print("-" * 38)
        print("  1. 🚀 启动 API 代理")
        print("  2. 🛑 停止 API 代理")
        print("  3. 🍻 部署/启动 傻酒馆 (SillyTavern)")
        print("  4. 🍷 停止 傻酒馆")
        print("  5. 🔄 一键更新 (代理与傻酒馆)")
        print("  0. 👋 退出控制台")
        print("="*38)
        
        choice = input(" 请输入指令并回车: ").strip()

        if choice == "1":
            if proxy_running: print("\n⚠️ 代理已运行！")
            else:
                p = subprocess.Popen([sys.executable, __file__, "run_app"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with open(PID_FILE, "w") as f: f.write(str(p.pid))
                time.sleep(1)
                print("\n✅ 代理启动成功！浏览器访问: 127.0.0.1:5000")
            input("\n👉 按回车键返回...")

        elif choice == "2":
            if proxy_running: kill_process(PID_FILE); print("\n✅ 代理已停止。")
            else: print("\n⚠️ 代理本来就是停止状态。")
            input("\n👉 按回车键返回...")

        elif choice == "3":
            if st_running:
                print("\n⚠️ 傻酒馆已在运行！浏览器访问: 127.0.0.1:8000")
            else:
                if not os.path.exists(ST_DIR):
                    print("\n📥 未检测到傻酒馆，正在自动化部署...")
                    os.system("pkg install nodejs git -y")
                    
                    print("📦 2/3 正在使用国内加速节点拉取仓库...")
                    mirrors = [
                        "https://kkgithub.com/SillyTavern/SillyTavern.git",
                        "https://mirror.ghproxy.com/https://github.com/SillyTavern/SillyTavern.git",
                        "https://github.moeyy.xyz/https://github.com/SillyTavern/SillyTavern.git"
                    ]
                    
                    success = False
                    for mirror in mirrors:
                        print(f"🔄 正在尝试节点: {mirror}")
                        ret = os.system(f"git clone {mirror} {ST_DIR}")
                        if ret == 0 and os.path.exists(ST_DIR):
                            success = True
                            break
                    
                    if not success:
                        print("\n❌ 糟糕，所有的国内加速节点都连不上！")
                        print("👉 建议开启科学上网工具后，再按 3 重试。")
                        input("\n按回车键返回菜单...")
                        continue # 核心拦截！直接退回菜单，不再触发那堆报错
                        
                    print("⏳ 3/3 首次安装依赖包 (可能需要几分钟)...")
                    os.system(f"cd {ST_DIR} && npm install")
                    print("\n✅ 部署完成！")
                
                # 再次安全检查：如果因为某些异常文件夹还是不在，彻底拦截
                if not os.path.exists(ST_DIR):
                    print("\n❌ 严重异常：找不到文件夹，启动终止。")
                    input("\n按回车键返回...")
                    continue

                print("\n🚀 正在后台启动傻酒馆...")
                p = subprocess.Popen(["node", "server.js"], cwd=ST_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with open(ST_PID_FILE, "w") as f: f.write(str(p.pid))
                time.sleep(3)
                print("✅ 傻酒馆已启动！请在浏览器访问: http://127.0.0.1:8000")
            input("\n👉 按回车键返回...")

        elif choice == "4":
            if st_running: kill_process(ST_PID_FILE); print("\n✅ 傻酒馆已安全退出。")
            else: print("\n⚠️ 傻酒馆并未运行。")
            input("\n👉 按回车键返回...")

        elif choice == "5":
            print("\n🔄 更新代码中...")
            os.system("git pull")
            if os.path.exists(ST_DIR): os.system(f"cd {ST_DIR} && git pull && npm install")
            print("\n✅ 全局更新完毕！(请重新启动生效)")
            proxy_update_msg, st_local, st_remote, st_status_msg = check_proxy_update(), *check_st_versions()
            input("\n👉 按回车键返回...")

        elif choice == "0":
            os.system("clear")
            sys.exit(0)
