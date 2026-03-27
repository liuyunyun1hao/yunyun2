🌸 YunYun AI 代理服务

YunYun Proxy 是一个轻量级、开箱即用的 API 代理工具，专为 硅基流动（SiliconFlow） API 设计，支持智能密钥轮询、故障转移、余额管理，并附带一个简洁的 Web 管理面板。
同时内置了 SillyTavern（傻酒馆） 的一键管理功能，让你在手机上也能轻松部署和使用大模型服务。

---

✨ 功能特点

· 🔑 多 API Key 管理 – 支持导入、删除、一键刷新余额，并自动按余额排序。

· 🔄 智能故障转移 – 自动尝试下一个可用的 Key，避免服务中断。

· 🌐 Web 管理面板 – 可视化管理密钥、测试连通性、导入/导出备份。

· 🍻 SillyTavern 集成 – 一键安装、启动、停止傻酒馆，并检测版本更新。

· 💾 数据加密存储 – 可选加密 keys_data.json，提升安全性。

· 📱 Termux 优化 – 支持在 Android 手机上运行，并提供开机自启教程。

---

🚀 部署指南（面向新手）

以下步骤以 Termux（Android） 为例，如果你在 Linux / macOS 上使用，原理相同。

1️⃣ 安装 Termux 并配置基础环境

1. 从 F-Droid 下载并安装 Termux（不要用 Google Play 的旧版）。
2. 打开 Termux，运行以下命令更新软件包：
   ```bash
   pkg update -y && pkg upgrade -y
   ```
3. 授予 Termux 存储权限（可选，用于备份）：
   ```bash
   termux-setup-storage
   ```

2️⃣ 安装必要依赖

```bash
pkg install python git nodejs -y
```

· python – 运行代理服务
· git – 克隆代码仓库
· nodejs – 运行 SillyTavern（如果需要）

3️⃣ 克隆项目

```bash
git clone https://github.com/liuyunyun1hao/yunyun2.git
cd yunyun2
```

4️⃣ 安装 Python 依赖

```bash
pip install flask requests cryptography
```

说明：cryptography 是可选的，如果不需要加密功能可以跳过，但推荐安装。

5️⃣ 启动代理服务

方式一：交互式菜单（推荐新手）

```bash
python proxy_server.py
```

你会看到一个图形化菜单：

```
╭──────────────────────────────╮
  🌸 YunYun AI 控制台 [v3.8]
╰──────────────────────────────╯

🔑 【API 本地代理】
 状态: 🔴 已停止  ✅(最新)
 🔗 网页: http://127.0.0.1:5000

🍻 【傻酒馆 SillyTavern】
 状态: 🔴 已停止
 版本: 未安装(本地) | 未知(最新)
 🔗 网页: http://127.0.0.1:8000

────────────────────────────────
  1. 启动代理    2. 停止代理
  3. 启动酒馆    4. 停止酒馆
  5. 一键更新    6. 自启教程
  0. 退出控制台
────────────────────────────────
 请输入数字指令: 
```

· 输入 1 即可启动代理（后台运行）。
· 启动成功后，打开手机浏览器访问 http://127.0.0.1:5000 进入管理面板。

方式二：直接后台启动

```bash
python proxy_server.py start --daemon
```

· 代理会在后台运行，PID 写入 server.pid。
· 停止代理：python proxy_server.py stop

6️⃣ 添加 API Key

1. 在浏览器中打开 http://127.0.0.1:5000
2. 在 控制台 页面：
   · 批量导入：每行一个 sk-xxx 格式的 Key，点击「解析导入」。
   · 手动添加：输入单个 Key 后点「添加」。
3. 点击「刷新余额」可以自动查询每个 Key 的余额。
4. 在表格中勾选一个 Key 作为当前使用的活动 Key。

7️⃣ （可选）启动 SillyTavern

在菜单中输入 3，程序会自动：

· 检查并安装 nodejs、git
· 克隆 SillyTavern 到 ~/SillyTavern
· 安装依赖并启动服务

启动后访问 http://127.0.0.1:8000 即可进入傻酒馆界面。

💡 提示：傻酒馆首次启动较慢，请耐心等待。
如果端口冲突，可以修改脚本中的 ST_PORT 变量。

---

🛠️ 使用管理面板

控制台

· 批量导入 Key：粘贴多行 sk-xxx 格式的密钥，一键导入。
· 手动添加：单独添加单个 Key。
· 刷新余额：遍历所有 Key 查询余额并排序（余额低的优先）。
· 启用 Key：在表格中点击单选框，选中当前使用的 Key。

连接测试

· 选择一个已启用的 Key。
· 输入测试内容（默认“讲个冷笑话”）。
· 点击「发送请求」，会调用 /v1/chat/completions 接口，返回模型的回答。
· 可以验证代理是否工作正常。

备份/恢复

· 导出当前配置：下载 keys_data.json 的备份文件。
· 从文件恢复：选择之前导出的 JSON 文件，恢复所有 Key 和激活状态。

---

📂 文件说明

文件 作用
proxy_server.py 主程序
keys_data.json 存储 API Key 和余额（可加密）
encrypt.key 加密密钥（若启用加密）
server.pid 代理服务的进程 ID
st_server.pid SillyTavern 的进程 ID
proxy.log 运行日志（自动轮转，保留 3 个 10MB）
backups/ 手动备份目录（可自行创建）

---

❓ 常见问题

1. 启动代理时提示端口被占用？

· 可能已有代理在运行，先用 2 停止再重试。
· 或者手动杀掉占用 5000 端口的进程：
  ```bash
  lsof -i :5000  # 查看PID
  kill -9 <PID>
  ```

2. 余额查询失败 / 网络异常？

· 检查手机网络，确保能访问 api.siliconflow.cn。
· 如果使用代理或 VPN，尝试关闭后再试。

3. 傻酒馆无法启动？

· 手动进入 ~/SillyTavern 目录，运行 node server.js 查看具体错误。
· 常见原因：端口冲突（8000 被占用）、依赖未安装完整。

4. 如何设置开机自启？

在 Termux 菜单中按 6 会显示自启教程，核心是编辑 ~/.bash_profile 添加以下内容：

```bash
if [ -z "$TMUX" ]; then
    cd ~/yunyun2 && python proxy_server.py
fi
```

保存后重启 Termux 即可自动进入控制台。

5. 如何更新程序？

· 在交互菜单中按 5 一键更新（会拉取最新代码并更新傻酒馆依赖）。
· 或者手动执行：
  ```bash
  git pull
  cd ~/SillyTavern && git pull && npm install
  ```

---

📜 版本历史

· v3.8 – 增加加密存储、余额排序、智能故障转移，优化移动端适配。
· 更早版本 – 基础代理功能、傻酒馆管理。

---

🧑‍💻 写在最后

YunYun 代理服务旨在让手机也能轻松使用大模型 API，并降低多 Key 管理的复杂度。
如果你觉得这个项目有用，欢迎 ⭐ 支持一下，也欢迎提交 Issue 或 PR 一起改进！

免责声明：本项目仅供学习交流，请勿用于非法用途。API Key 请妥善保管。
