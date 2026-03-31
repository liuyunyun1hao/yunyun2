请依次复制以下命令，每一段复制并在 Termux 中粘贴回车，等它跑完（出现 $ 符号提示符）再执行下一步：
第一步：更新系统并安装环境与底层库
这一步会把 Git、Python、Node.js（酒馆需要），以及刚才报错的 cryptography 的官方安卓预编译版一次性装好。



pkg update -y && pkg install -y git python nodejs python-cryptography

第二步：克隆你的代码仓库
我们依然使用镜像节点，防止网络问题导致找不到文件夹。



cd ~ && git clone https://github.com/liuyunyun1hao/yunyun2.git

第三步：安装剩余的 Python 轻量依赖
进入文件夹，用 pip 安装不需要底层编译的 flask 和 requests。



cd ~/yunyun2 && pip install flask requests

第四步：手动启动控制台
环境全部配置完毕，直接用 Python 运行你的主程序：



cd ~/yunyun2 && python proxy_server.py



💡 日常使用提示：
因为我们取消了快捷指令，以后你每次重新打开 Termux 想要启动这个面板时，只需要输入第四步的命令即可：
cd ~/yunyun2 && python proxy_server.py
