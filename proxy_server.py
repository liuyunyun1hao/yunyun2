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

# === 🌟 重新设计的“少女心风格”淡粉色前端 🌟 ===
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>云云 AI 助理</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css" />
    <script src="https://unpkg.com/element-plus"></script>
    <style>
        /* 定义少女心淡粉色系变量 */
        :root { 
            --girl-bg: #fff0f3; /* 极淡的粉色背景 */
            --girl-card: #ffffff; 
            --girl-pink: #ff8fa3; /* 少女粉主色调 */
            --girl-pink-light: #ffc0cb; /* 辅色调 */
            --girl-text: #5e548e; /* 柔和的深紫色文字 */
            --girl-subtext: #a19db8; 
            --girl-shadow: rgba(255, 143, 163, 0.1); /* 粉色调阴影 */
        }
        
        body { font-family: -apple-system, sans-serif; background-color: var(--girl-bg); color: var(--girl-text); margin: 0; padding: env(safe-area-inset-top) 16px env(safe-area-inset-bottom) 16px; -webkit-font-smoothing: antialiased; }
        
        /* 贴合手机端的卡片式 UI */
        .app-container { max-width: 600px; margin: 0 auto; padding-bottom: 20px;}
        
        /* 粉色大标题 */
        .page-header { text-align: center; color: var(--girl-pink); padding: 20px 0 10px 0; letter-spacing: -1px; }
        .page-header h1 { font-size: 24px; margin: 0; font-weight: 700;}
        .page-header span { font-size: 13px; color: var(--girl-subtext); }

        /* iOS/手机风格卡片 */
        .ios-card { background: var(--girl-card); border-radius: 20px; padding: 16px; box-shadow: 0 6px 20px var(--girl-shadow); margin-bottom: 16px; border: 1px solid rgba(255,192,203,0.3);}
        .card-title { font-size: 18px; font-weight: 600; margin: 0 0 16px 0; color: var(--girl-text); display: flex; justify-content: space-between; align-items: center;}
        
        /* Element Plus 粉色化自定义 */
        .el-button { border-radius: 12px !important; font-weight: 600 !important; }
        
        /* 主按钮：粉色渐变 */
        .el-button--primary { 
            background: linear-gradient(135deg, #ffc0cb, #ff8fa3) !important; 
            border: none !important; 
            color: white !important;
            transition: transform 0.1s ease;
        }
        .el-button--primary:active { transform: scale(0.97); }

        /* 标签：粉色系 */
        .el-tag { background-color: #fff0f3 !important; color: #ff8fa3 !important; border: 1px solid #ffc0cb !important; border-radius: 6px !important;}

        /* 输入框：粉色边框聚焦 */
        .el-input__wrapper, .el-textarea__inner { border-radius: 14px !important; box-shadow: 0 0 0 1px #ffc0cb inset !important; background-color: #fafafa !important; }
        .el-input__wrapper.is-focus, .el-textarea__inner:focus { box-shadow: 0 0 0 2px var(--girl-pink-light) inset !important; background-color: #fff !important; }
        
        /* 表格：粉色头部与柔和背景 */
        .el-table { border-radius: 14px; overflow: hidden; border: none !important; color: var(--girl-text) !important;}
        .el-table__inner-wrapper::before { display: none !important;}
        .el-table th.el-table__cell { background-color: #fff0f3 !important; color: #ff8fa3; font-weight: 600; font-size: 13px; border-bottom: none !important;}
        .el-table .el-table__cell { border-bottom: 1px solid rgba(255,192,203,0.1) !important;}
        .el-table__empty-text { color: var(--girl-subtext); }
        .el-table__row--striped td.el-table__cell { background-color: rgba(255,240,243,0.3) !important; }

        /* 单选框和开关：粉色 */
        .el-radio__input.is-checked .el-radio__inner { background-color: var(--girl-pink) !important; border-color: var(--girl-pink) !important; }
        .el-radio__input.is-checked + .el-radio__label { color: var(--girl-pink) !important; font-weight: 600;}
        .el-radio__inner { width: 18px; height: 18px;}

        /* 手机端底部的测试区域 */
        .test-box { background: #fafafa; padding: 12px; border-radius: 16px; margin-top: 16px; border: 1px solid #ffc0cb;}
    </style>
</head>
<body>
<div id="app" class="app-container">
    <div class="page-header">
        <h1>🌸 云云 AI 助理</h1>
        <span>SiliconFlow 专属代理节点 (http://127.0.0.1:5000/v1)</span>
    </div>

    <el-collapse class="ios-card" style="border: none; padding: 0;">
        <el-collapse-item name="1">
            <template #title>
                <span style="font-size: 16px; font-weight: 600; color: var(--girl-pink);">🔑 批量导入 Key</span>
            </template>
            <el-input type="textarea" v-model="batchKeys" placeholder="在此粘贴多个 Key，每行一个" :rows="3"></el-input>
            <div style="margin-top: 12px; display: flex; gap: 10px;">
                <el-button type="primary" @click="importKeys">解析并导入</el-button>
                <el-button @click="checkAllBalances" :loading="checking">刷新余额并排序</el-button>
            </div>
        </el-collapse-item>
    </el-collapse>

    <div class="ios-card">
        <h2 class="card-title">📱 运行状态</h2>
        <el-table :data="keys" style="width: 100%" empty-text="未导入 Key">
            <template #append>
                <div v-if="!activeKey && keys.length > 0" style="color: #ff3b30; font-size: 13px; text-align: center; padding: 10px 0;">⚠️ 请至少启用一个 Key</div>
            </template>
            <el-table-column label="启用" width="60" align="center">
                <template #default="scope">
                    <el-radio v-model="activeKey" :label="scope.row.key" @change="saveData"><span></span></el-radio>
                </template>
            </el-table-column>
            <el-table-column label="Key" min-width="150">
                <template #default="scope">
                    <el-tag size="small" type="primary">{{ maskKey(scope.row.key) }}</el-tag>
                </template>
            </el-table-column>
            <el-table-column prop="balance" label="余额" width="70" align="center"></el-table-column>
            <el-table-column label="操作" width="60" align="center">
                <template #default="scope"><el-button size="small" type="danger" text @click="deleteKey(scope.$index)">删除</el-button></template>
            </el-table-column>
        </el-table>
    </div>

    <div class="ios-card">
        <h2 class="card-title">⚡ 快速测试舱</h2>
        <p style="color: var(--girl-subtext); font-size: 13px; margin: -10px 0 10px 0;">不打开 AI 软件，在此测试当前 Key 是否存活。</p>
        
        <div v-if="!activeKey" style="color: #ffc0cb; text-align: center; padding: 10px 0;">(请先启用一个 Key)</div>
        
        <div v-else>
            <el-input type="textarea" v-model="testPrompt" placeholder="讲个冷笑话。" :rows="2"></el-input>
            <div style="margin-top: 12px; display: flex; gap: 10px;">
                <el-button type="primary" @click="sendTest" :loading="isTesting">发送测试</el-button>
                <el-button @click="sendTest" :loading="isTesting">重回</el-button>
                <el-button @click="copyText('http://127.0.0.1:5000/v1')">复制代理地址</el-button>
            </div>
            <el-input v-if="testResult" type="textarea" v-model="testResult" :rows="5" readonly style="margin-top: 16px; border: 1px solid #ffc0cb; border-radius: 12px;"></el-input>
        </div>
    </div>
</div>
<script>
    const { createApp, ref, onMounted } = Vue;
    createApp({
        setup() {
            const keys = ref([]), activeKey = ref(null), batchKeys = ref(''), checking = ref(false);
            const testPrompt = ref('讲个冷笑话。'), testResult = ref(''), isTesting = ref(false);

            const loadData = async () => { const res = await fetch('/api/data'); const data = await res.json(); keys.value = data.keys || []; activeKey.value = data.active_key; };
            const saveData = async () => { const res = await fetch('/api/data', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ keys: keys.value, active_key: activeKey.value }) }); const result = await res.json(); keys.value = result.data.keys; };
            const maskKey = (key) => key ? key.substring(0, 6) + '...' + key.substring(key.length - 4) : '';
            const importKeys = async () => {
                const newKeys = batchKeys.value.split('\\n').map(k => k.trim()).filter(k => k.startsWith('sk-'));
                if (newKeys.length === 0) return ElementPlus.ElMessage.warning('未检测到有效 Key');
                newKeys.forEach(k => { if (!keys.value.some(exist => exist.key === k)) keys.value.push({ key: k, balance: '未知' }); });
                batchKeys.value = ''; await saveData(); ElementPlus.ElMessage({ message: '导入成功!', type: 'success' });
            };
            const deleteKey = async (index) => { if (keys.value[index].key === activeKey.value) activeKey.value = null; keys.value.splice(index, 1); await saveData(); };
            const checkAllBalances = async () => {
                checking.value = true;
                for (let i = 0; i < keys.value.length; i++) {
                    keys.value[i].balance = '...';
                    try { const res = await fetch('/api/check_balance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: keys.value[i].key }) }); const data = await res.json(); keys.value[i].balance = data.balance; } catch (e) { keys.value[i].balance = '超时'; }
                }
                await saveData(); checking.value = false; ElementPlus.ElMessage({ message: '排序完毕啦!', type: 'success' });
            };
            const copyText = (text) => { navigator.clipboard.writeText(text).then(() => ElementPlus.ElMessage({ message: '已复制接口地址~', type: 'success' })); };
            const sendTest = async () => {
                if (!activeKey.value || !testPrompt.value.trim()) return;
                isTesting.value = true; testResult.value = '请求发送中...稍等哦...';
                try {
                    const response = await fetch('/v1/chat/completions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: "Qwen/Qwen2.5-7B-Instruct", messages: [{ role: "user", content: testPrompt.value }] }) });
                    const data = await response.json();
                    testResult.value = data.choices ? data.choices[0].message.content : `错误啦: ${JSON.stringify(data)}`;
                } catch (error) { testResult.value = `请求失败: ${error.message}`; } finally { isTesting.value = false; }
            };
            onMounted(() => loadData());
            return { keys, activeKey, batchKeys, checking, testPrompt, testResult, isTesting, importKeys, checkAllBalances, deleteKey, maskKey, saveData, copyText, sendTest };
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
            os.kill(pid, 0)
            return True
        except (OSError, ValueError):
            os.remove(PID_FILE)
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_app":
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(host="0.0.0.0", port=5000, use_reloader=False)
        sys.exit(0)

    # ============ 终端交互界面 ============
    while True:
        os.system("clear")
        print("\n\033[1;35m==================================")
        print(" 🌸 YunYun API Proxy 快捷控制台")
        print("==================================\033[0m")
        
        is_running = check_status()
        # 状态也变成粉色系
        status_text = "\033[1;92m💖 助理正在悄悄工作 (http://127.0.0.1:5000)\033[0m" if is_running else "\033[1;31m🔴 助理正在休息\033[0m"
        
        print(f" 当前状态: {status_text}")
        print("----------------------------------")
        print("  \033[1;35m1.\033[0m 请助理开始工作")
        print("  \033[1;35m2.\033[0m 请助理去休息")
        print("  \033[1;35m3.\033[0m 同步 GitHub 最新少女心代码")
        print("  \033[1;35m0.\033[0m 退出菜单 (助理还在工作哦)")
        print("==================================")
        
        choice = input(" 输入数字并回车: ").strip()

        if choice == "1":
            if is_running:
                print("\n⚠️ 助理已经在为你工作啦，不需要重新启动哦。")
            else:
                print("\n🚀 正在请助理悄悄在后台工作...")
                p = subprocess.Popen([sys.executable, __file__, "run_app"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with open(PID_FILE, "w") as f:
                    f.write(str(p.pid))
                time.sleep(1.5)
                print("✅ 成功！你可以去手机浏览器看可爱的助理了。")
            input("\n👉 按回车键返回菜单...")

        elif choice == "2":
            if is_running:
                print("\n🛑 正在请助理去休息...")
                with open(PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    pass
                os.remove(PID_FILE)
                print("✅ 好的，助理去休息了。")
            else:
                print("\n⚠️ 助理本来就在休息状态中呀。")
            input("\n👉 按回车键返回菜单...")

        elif choice == "3":
            print("\n🔄 正在从 GitHub 同步你的最新代码...\n")
            os.system("git pull")
            print("\n✅ 更新完毕！(更新后，请按 2 请旧助理休息，再按 1 请新助理上岗)")
            input("\n👉 按回车键返回菜单...")

        elif choice == "0":
            print("\n👋 拜拜！")
            if check_status():
                print("\033[1;35m💡 提示：云云助理依然在【后台】为你静默工作着。")
                print("打开任何 AI 软件，它都已经准备好为你聚合 Key 了。\033[0m")
            sys.exit(0)
            
        else:
            print("\n❌ 输入无效，请输入 0, 1, 2, 或 3。")
            time.sleep(1)
