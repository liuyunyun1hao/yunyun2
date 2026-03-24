# 🌸 硅基流动多 Key 本地代理工具

这是一个跑在本地（手机 Termux 或电脑端）的轻量级 API 代理服务。专为经常使用 **硅基流动 (SiliconFlow)** 接口，且手里有多个 API Key 的朋友编写。

**核心痛点解决**：如果直接在 AI 软件里频繁切换多个硅基流动的 Key，同一个 IP 下很容易被系统风控导致 Key 无法使用。本工具通过建立本地代理，让你在网页端单独选定一个 Key 转发请求，完美规避并发风控，且不用在 AI 软件里来回改配置。

## ✨ 核心功能

* **🛡️ 纯本地超安全**：不依赖任何第三方服务器，Key 全部保存在你自己的本地文件 (`keys_data.json`) 里。
* **💰 余额管理大师**：支持批量复制粘贴导入 Key，一键查询所有余额，并**自动按余额从小到大排序**，优先消耗零钱。
* **🎯 精准单点调用**：在网页端勾选你想用的那个 Key，代理服务器会自动把它替换进 API 请求中。
* **📱 绝美粉色 UI**：自带一个淡粉色 iOS 毛玻璃质感的本地网页控制台，手机端完美适配。
* **⚡ 内置测试舱**：网页端自带连通性测试模块，不用打开 AI 软件就能测 Key 是死是活。

---

## 🚀 部署与使用方法 (以安卓 Termux 为例)

### 1. 首次安装
打开你的 Termux，直接复制并执行以下所有命令：

```bash
pkg update && pkg upgrade -y
pkg install git python -y
pip install flask requests
git clone [https://github.com/liuyunyun1hao/yunyun2.git](https://github.com/liuyunyun1hao/yunyun2.git)
cd yunyun2
python proxy_server.py

提示：启动后，终端会变成一个全中文的交互菜单，输入 1 即可启动后台服务。
2. 设置 Termux 每次打开自动启动
为了不用每次进 Termux 都敲代码，你可以配置开机自启。在 Termux 终端输入以下命令回车即可：
echo 'if [ -z "$TMUX" ]; then cd ~/yunyun2 && python proxy_server.py; fi' >> ~/.bash_profile

3. 如何在 AI 软件中配置？
服务启动后，打开你的手机浏览器，访问：http://127.0.0.1:5000，导入并勾选你要用的 Key。
然后去你的 AI 软件（如 NextChat, Chatbox 等）中设置：
 * API 接口地址 / Base URL：填写 http://127.0.0.1:5000/v1
 * API Key：随便填几个字母即可（比如 sk-123），因为本地代理会自动帮你替换成你网页上勾选的真实 Key。
🔄 如何更新版本？
如果 GitHub 上的代码有更新，你可以极其简单地完成升级：
 * 打开 Termux 终端（或者通过刚才设置的自启直接进入控制台菜单）。
 * 在中文菜单中输入 3 并回车。
 * 系统会自动从 GitHub 拉取最新代码。
 * 按 2 停止旧服务，再按 1 重新启动，即可享受新版本。
