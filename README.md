
# 硅基流动 API Key 批量管理面板 & 酒馆 (1.13) 部署方案

这是一个轻量级且高效的工具，主要用于**批量管理硅基流动 (SiliconFlow) API Key**。搭配内置的前置网站服务，可实现接口的稳定直连。

同时，本项目专为安卓手机的 **Termux** 环境进行了优化，集成了 Node.js 和 Python 环境，能够顺滑部署并运行**固定版本（1.13）的酒馆 (SillyTavern)**，解决了常见的底层加密库（如 `cryptography`）编译报错问题。

## ✨ 核心功能

- **🔑 API 批量管理**：提供可视化的前置网站，轻松添加、管理和调用硅基流动 API Key。
- **⚡ 直连访问**：内置代理服务端，解决网络连通性问题，实现直连。
- **📱 纯手机部署**：完美适配 Termux 环境，提供傻瓜式的依赖安装方案。
- **🍺 兼容酒馆 1.13**：一键安装 Node.js 与 Python 运行环境，为部署 1.13 版本的酒馆打好底层基础。

---

## 🛠️ Termux 一键安装与部署指南

请确保你的安卓手机已安装 Termux。打开 Termux 后，**请依次复制以下每一段命令**，粘贴并回车。等待当前命令跑完（出现 `$` 符号提示符）后再执行下一步：

### 第一步：更新系统并安装环境与底层库
这一步会把 Git、Python、Node.js（酒馆运行必须），以及官方安卓预编译版的 `cryptography`（防止编译报错）一次性装好。

```bash
pkg update -y && pkg install -y git python nodejs python-cryptography
```

第二步：克隆代码仓库
使用 GitHub 镜像节点拉取代码，防止网络问题导致拉取失败或找不到文件夹。

```bash
cd ~ && git clone https://github.com/liuyunyun1hao/yunyun2.git
```

第三步：安装剩余的 Python 轻量依赖
进入项目文件夹，使用 pip 安装不需要底层编译的 web 框架和请求库。

```bash
cd ~/yunyun2 && pip install flask requests
```

第四步：手动启动控制台
环境全部配置完毕！直接使用 Python 运行主程序服务：

```bash
cd ~/yunyun2 && python proxy_server.py
```

💡 日常使用提示
为了保持系统的干净纯粹，本项目没有强制设置开机自启或快捷指令。以后每次重新打开 Termux 想要启动面板时，只需要输入以下命令即可：

```bash
cd ~/yunyun2 && python proxy_server.py
```

