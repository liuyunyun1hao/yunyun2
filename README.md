🌸 YunYun AI 代理服务

https://img.shields.io/badge/version-3.8-brightgreen
https://img.shields.io/badge/license-MIT-blue

YunYun AI 代理服务是一个轻量级代理工具，主要用于为 硅基流动（SiliconFlow）API 提供统一接入、智能密钥轮询与故障转移，同时支持一键管理 SillyTavern（傻酒馆） 的启动与停止。
项目内置 Web 管理面板，支持密钥批量导入、余额查询、备份恢复等功能，尤其适合在 Termux 或 Linux 服务器 上长期运行。

---

✨ 主要功能

· 🔑 智能密钥代理
    支持多 API Key 自动轮询，请求失败（401/403/429/超时）时自动切换，保障服务稳定。
· 📊 Web 管理面板
    可视化管理密钥列表，支持余额查询、批量导入、手动添加、备份恢复。
· ⚙️ SillyTavern 一键管理
    集成傻酒馆的自动部署、启动与停止，无需手动配置 Node.js 环境。
· 🔒 数据加密存储（可选）
    可对保存的密钥进行加密，防止明文泄露。
· 🚀 Termux 友好
    提供一键自启配置脚本，适合在 Android 设备上长期运行。

---

📦 部署与启动

1️⃣ 环境要求

· Python 3.7+
· pip（安装依赖）
· 可选：cryptography（用于数据加密）

2️⃣ 克隆项目

```bash
git clone https://github.com/liuyunyun1hao/yunyun2.git
cd yunyun2
```

3️⃣ 安装依赖

```bash
pip install flask requests cryptography
```

若无需加密，可不安装 cryptography

4️⃣ 启动服务

方式一：交互菜单（推荐）

```bash
python proxy_server.py
```

进入菜单后：

· 输入 1 启动代理（后台运行）
· 输入 3 启动傻酒馆（自动部署）

方式二：直接后台运行

```bash
python proxy_server.py start --daemon   # 启动代理
python proxy_server.py start-st --daemon # 启动傻酒馆
python proxy_server.py stop              # 停止代理
python proxy_server.py stop-st           # 停止傻酒馆
```

---

🌐 使用说明

代理地址

· API 端点：http://127.0.0.1:5000/v1
· Web 管理面板：http://127.0.0.1:5000

在 SillyTavern 中配置

1. 打开傻酒馆 → API 连接设置
2. 选择 Chat Completion 接口
3. 填入代理地址：http://127.0.0.1:5000/v1
4. 无需填写 API Key（由代理自动轮询）
5. 模型选择如 Qwen/Qwen2.5-7B-Instruct 等

管理面板功能

· 控制台：查看/添加/删除密钥，设置默认 Key，批量导入
· 连接测试：选择活动 Key，发送测试对话
· 备份/恢复：导出或导入配置文件（JSON 格式）

---

📁 文件说明

文件 说明
proxy_server.py 主程序（含 Web 代理 + 管理界面）
keys_data.json 密钥存储文件（可加密）
encrypt.key 加密密钥（自动生成，需妥善保管）
proxy.log 运行日志（自动轮转）
backups/ 手动备份目录（通过面板导出）
server.pid 代理进程 PID
st_server.pid 傻酒馆进程 PID

---

🔧 高级配置

修改端口

编辑 proxy_server.py 中的 PORT 和 ST_PORT 变量：

```python
PORT = 5000        # 代理端口
ST_PORT = 8000     # 傻酒馆端口
```

调整故障转移策略

```python
RETRY_COUNT = 2        # 失败后最多尝试的 Key 数量
REQUEST_TIMEOUT = (5, 60)  # (连接超时, 读取超时)
```

开启数据加密

程序首次启动时若检测到 cryptography 已安装，会自动生成 encrypt.key 并对 keys_data.json 加密。
⚠️ 请务必备份 encrypt.key，否则数据将无法恢复！

---

🛠 Termux 自启教程（可选）

1. 在 Termux 中运行以下命令（确保已安装 python 和 git）：

```bash
echo 'if [ -z "$TMUX" ]; then cd ~/yunyun2 && python proxy_server.py; fi' >> ~/.bash_profile
source ~/.bash_profile
```

1. 下次打开 Termux 时，程序会自动进入交互菜单，输入 1 即可后台运行代理。

---

🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request，帮助改进项目。

---

📄 许可证

本项目基于 MIT 协议开源，详情见 LICENSE 文件。

---

Made with ❤️ by liuyunyun1hao
