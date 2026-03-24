import os
import json
from flask import Flask, request, jsonify, Response
import requests

app = Flask(__name__)
DATA_FILE = "keys_data.json"
API_BASE = "https://api.siliconflow.cn/v1"

# === 数据管理 ===
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"keys": [], "active_key": None}

def save_data(data):
    # 按照余额从小到大排序
    def get_balance_val(item):
        try:
            return float(item.get("balance", 0))
        except:
            return float('inf')
            
    data["keys"] = sorted(data["keys"], key=get_balance_val)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# === 路由 ===
@app.route("/")
def index():
    return HTML_CONTENT

@app.route("/api/data", methods=["GET", "POST"])
def manage_data():
    if request.method == "POST":
        data = request.json
        save_data(data)
        return jsonify({"status": "success", "data": load_data()})
    return jsonify(load_data())

@app.route("/api/check_balance", methods=["POST"])
def check_balance():
    key = request.json.get("key")
    try:
        headers = {"Authorization": f"Bearer {key}"}
        res = requests.get(f"{API_BASE}/user/info", headers=headers, timeout=10)
        res_data = res.json()
        if res.status_code == 200 and "data" in res_data:
            balance = res_data["data"].get("totalBalance", "获取失败")
            return jsonify({"balance": balance})
    except Exception:
        pass
    return jsonify({"balance": "错误"})

@app.route("/v1/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def proxy(path):
    data = load_data()
    active_key = data.get("active_key")
    
    if not active_key:
        return jsonify({"error": "未选择活动 Key，请在前端配置"}), 400

    url = f"{API_BASE}/{path}"
    headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'authorization']}
    headers["Authorization"] = f"Bearer {active_key}"

    stream = False
    if request.is_json:
        stream = request.json.get("stream", False)

    try:
        resp = requests.request(
            method=request.method, url=url, headers=headers,
            data=request.get_data(), stream=stream, timeout=60
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        resp_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                        if name.lower() not in excluded_headers]
        return Response(resp.iter_content(chunk_size=1024), resp.status_code, resp_headers)
    except Exception as e:
        return jsonify({"error": f"代理请求失败: {str(e)}"}), 500


# === 极简 iOS 风格前端 ===
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>API Proxy Console</title>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/element-plus/dist/index.css" />
    <script src="https://unpkg.com/element-plus"></script>
    <style>
        :root { --ios-bg: #f2f2f7; --ios-card: #ffffff; --ios-blue: #007aff; --ios-text: #1c1c1e; --ios-subtext: #8e8e93; }
        body { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif; background-color: var(--ios-bg); color: var(--ios-text); margin: 0; padding: 16px; -webkit-font-smoothing: antialiased; }
        .app-container { max-width: 800px; margin: 0 auto; }
        
        /* iOS 分段控制器 (Tabs) */
        .segmented-control { display: flex; background: #e3e3e8; border-radius: 8px; padding: 2px; margin-bottom: 20px; }
        .segment { flex: 1; text-align: center; padding: 6px 0; font-size: 14px; font-weight: 500; cursor: pointer; border-radius: 6px; color: var(--ios-text); transition: all 0.2s ease; }
        .segment.active { background: var(--ios-card); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        
        /* 卡片视图 */
        .ios-card { background: var(--ios-card); border-radius: 16px; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); margin-bottom: 20px; }
        .card-title { font-size: 20px; font-weight: 600; margin: 0 0 16px 0; letter-spacing: -0.5px; }
        
        /* 覆盖 Element Plus 样式以贴合 iOS */
        .el-button { border-radius: 8px !important; font-weight: 500 !important; }
        .el-button--primary { background-color: var(--ios-blue) !important; border-color: var(--ios-blue) !important; }
        .el-input__wrapper, .el-textarea__inner { border-radius: 10px !important; box-shadow: 0 0 0 1px #e5e5ea inset !important; background-color: #fafafa !important; }
        .el-input__wrapper.is-focus, .el-textarea__inner:focus { box-shadow: 0 0 0 1px var(--ios-blue) inset !important; background-color: #fff !important; }
        .el-table { border-radius: 12px; overflow: hidden; border: 1px solid #e5e5ea; }
        .el-table th.el-table__cell { background-color: #f9f9eb !important; color: var(--ios-subtext); font-weight: 500; }
        
        /* 教程排版 */
        .tutorial-block { background: #f9f9f9; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
        .tutorial-title { font-size: 16px; font-weight: 600; margin-bottom: 8px; color: var(--ios-blue); }
        .code-snippet { background: #282c34; color: #abb2bf; padding: 12px; border-radius: 8px; font-family: monospace; overflow-x: auto; font-size: 13px; margin: 8px 0; }
    </style>
</head>
<body>
<div id="app" class="app-container">
    <div class="segmented-control">
        <div class="segment" :class="{active: activeTab === 'console'}" @click="activeTab = 'console'">控制台</div>
        <div class="segment" :class="{active: activeTab === 'tutorial'}" @click="activeTab = 'tutorial'">部署与更新教程</div>
    </div>

    <div v-show="activeTab === 'console'">
        <div class="ios-card">
            <h2 class="card-title">🔑 批量导入与检测</h2>
            <el-input type="textarea" v-model="batchKeys" placeholder="在此粘贴多个 Key，每行一个 (sk-...)" :rows="4"></el-input>
            <div style="margin-top: 16px; display: flex; gap: 12px;">
                <el-button type="primary" @click="importKeys">解析导入</el-button>
                <el-button @click="checkAllBalances" :loading="checking">一键刷新余额</el-button>
            </div>
        </div>

        <div class="ios-card">
            <h2 class="card-title">📱 代理节点状态</h2>
            <p style="color: var(--ios-subtext); font-size: 13px; margin-top: -10px;">代理地址: http://127.0.0.1:5000/v1 (请填写至 AI 软件)</p>
            <el-table :data="keys" style="width: 100%">
                <el-table-column label="启用" width="70" align="center">
                    <template #default="scope">
                        <el-radio v-model="activeKey" :label="scope.row.key" @change="saveData"><span></span></el-radio>
                    </template>
                </el-table-column>
                <el-table-column label="API Key" min-width="180">
                    <template #default="scope">
                        <span style="font-family: monospace;">{{ maskKey(scope.row.key) }}</span>
                    </template>
                </el-table-column>
                <el-table-column prop="balance" label="余额" width="90" align="center"></el-table-column>
                <el-table-column label="操作" width="80" align="center">
                    <template #default="scope">
                        <el-button size="small" type="danger" text @click="deleteKey(scope.$index)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </div>
    </div>

    <div v-show="activeTab === 'tutorial'" class="ios-card">
        <h2 class="card-title">📖 部署与更新教程</h2>
        
        <div class="tutorial-block">
            <div class="tutorial-title">1. GitHub 仓库初始化</div>
            <p style="font-size: 14px; margin: 5px 0;">在 GitHub 新建仓库，添加文件 <code>proxy_server.py</code>，将所有代码粘贴进去并保存。</p>
        </div>

        <div class="tutorial-block">
            <div class="tutorial-title">2. Termux 首次部署环境</div>
            <p style="font-size: 14px; margin: 5px 0;">在手机 Termux 中依次执行以下命令：</p>
            <div class="code-snippet">
pkg update && pkg upgrade -y<br>
pkg install git python -y<br>
pip install flask requests<br>
git clone https://github.com/你的用户名/你的仓库名.git<br>
cd 你的仓库名<br>
python proxy_server.py
            </div>
        </div>

        <div class="tutorial-block">
            <div class="tutorial-title">3. 如何更新代码 (重要)</div>
            <p style="font-size: 14px; margin: 5px 0;">当你以后在 GitHub 上修改了代码，只需在 Termux 中停止服务（按 <code>Ctrl+C</code>），然后拉取最新代码：</p>
            <div class="code-snippet">
cd 你的仓库名<br>
git pull<br>
python proxy_server.py
            </div>
        </div>

        <div class="tutorial-block">
            <div class="tutorial-title">4. 后台保活防查杀</div>
            <p style="font-size: 14px; margin: 5px 0;">为了防止息屏后代理失效，请在 Termux 中执行：</p>
            <div class="code-snippet">termux-wake-lock</div>
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
            const checking = ref(false);

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

            const maskKey = (key) => key ? key.substring(0, 6) + '...' + key.substring(key.length - 4) : '';

            const importKeys = async () => {
                const newKeys = batchKeys.value.split('\\n').map(k => k.trim()).filter(k => k.startsWith('sk-'));
                if (newKeys.length === 0) return ElementPlus.ElMessage.warning('未检测到有效 Key');
                
                let added = 0;
                newKeys.forEach(k => {
                    if (!keys.value.some(exist => exist.key === k)) {
                        keys.value.push({ key: k, balance: '未知' });
                        added++;
                    }
                });
                batchKeys.value = '';
                await saveData();
                ElementPlus.ElMessage.success(`导入 ${added} 个 Key`);
            };

            const deleteKey = async (index) => {
                if (keys.value[index].key === activeKey.value) activeKey.value = null;
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
                        keys.value[i].balance = '超时';
                    }
                }
                await saveData();
                checking.value = false;
                ElementPlus.ElMessage.success('余额已刷新并重新排序');
            };

            onMounted(() => loadData());
            return { activeTab, keys, activeKey, batchKeys, checking, importKeys, checkAllBalances, deleteKey, maskKey, saveData };
        }
    }).use(ElementPlus).mount('#app');
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
