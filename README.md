# YunYun AI 代理服务 (Render 云端部署版)

这是一个专为Render免费部署优化的AI API代理服务，支持硅基流动(DeepSeek)等大语言模型的API代理功能，提供密钥管理、故障转移和访问控制。

## 特性

- 🔄 **智能密钥轮询**: 自动在多个API密钥之间切换，提高可用性
- 🔒 **双重认证保护**: 支持API密钥认证和HTTP Basic认证
- 🛡️ **密钥加密存储**: 可选加密存储API密钥
- 🌐 **云端部署**: 专为Render等云平台优化
- 📱 **多设备访问**: 可在不同设备上访问
- 💰 **完全免费**: 适配Render免费套餐

## 部署到Render

### 方法1: 一键部署 (最简单)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**注意**: 你需要有一个GitHub账号并将此代码上传到GitHub仓库。

### 方法2: 手动部署

1. **注册Render账号**
   - 访问 [render.com](https://render.com)
   - 使用GitHub账号登录（推荐）
   - 完成邮箱验证

2. **创建新Web Service**
   - 点击 "New +" → "Web Service"
   - 连接你的GitHub仓库
   - 选择要部署的分支

3. **配置设置**
   - **Name**: `yunyun-proxy` (自定义名称)
   - **Region**: `Singapore` (推荐，连接中国更稳定)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python proxy_server_render.py`

4. **配置环境变量** (重要!)
   
   在Render仪表板的 "Environment" 标签页中，添加以下环境变量：

   | 变量名 | 说明 | 示例值 | 必需 |
   |--------|------|--------|------|
   | `AUTH_USERNAME` | 管理界面用户名 | `admin` | 否 |
   | `AUTH_PASSWORD` | 管理界面密码 | `your_secure_password` | 是(如果想保护) |
   | `REQUIRE_AUTH` | 是否要求认证 | `true` | 否 |
   | `API_KEY` | API密钥认证 | `your_api_key_here` | 否 |
   | `USE_API_KEY_AUTH` | 使用API密钥认证 | `false` | 否 |
   | `ENCRYPT_ENABLED` | 启用密钥加密 | `true` | 否 |
   | `ENCRYPTION_KEY` | 加密密钥（可选） | 自动生成 | 否 |

   **重要**: 如果想保护服务不被公开访问，请设置 `REQUIRE_AUTH=true` 并设置密码或API密钥。

5. **启动部署**
   - 点击 "Create Web Service"
   - Render会自动构建和部署
   - 等待约5分钟完成部署

## 使用方法

### 1. 访问管理界面

部署完成后，访问你的服务地址（如 `https://yunyun-proxy.onrender.com`）：
- 如果设置了认证，会要求输入用户名密码
- 进入管理界面后可以看到快速使用指南

### 2. 首次设置密钥

**方法A: 通过管理界面导入**
1. 访问 `/api/data` 端点（需认证）
2. 使用POST请求导入密钥数据

**方法B: 使用curl命令**
```bash
curl -X POST "https://your-service.onrender.com/api/data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)" \
  -d '{
    "keys": [
      {
        "key": "sk-your-siliconflow-key-here",
        "balance": "未知",
        "fail_count": 0
      }
    ],
    "active_key": "sk-your-siliconflow-key-here"
  }'
```

### 3. 测试代理服务

```bash
curl -X POST "https://your-service.onrender.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'admin:password' | base64)" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {
        "role": "user",
        "content": "你好，讲个笑话"
      }
    ],
    "stream": false
  }'
```

### 4. 在其他应用中使用

#### SillyTavern:
1. 打开SillyTavern设置
2. 进入 "AI Response Configuration"
3. 在API URL中输入: `https://your-service.onrender.com/v1`
4. 在API Key中输入管理认证信息
5. 选择模型

#### OpenCat/ChatKit等客户端:
- 设置自定义API端点: `https://your-service.onrender.com/v1`
- 添加认证头

## 认证方式

### 1. Basic HTTP认证 (默认)
在请求头中添加:
```
Authorization: Basic [base64编码的用户名:密码]
```

### 2. API密钥认证 (可选)
在请求头中添加:
```
X-API-Key: [你的API密钥]
```

### 3. 不认证 (不推荐)
设置 `REQUIRE_AUTH=false`，但这样任何人都可以访问你的服务。

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | `5000` | 服务端口，Render会自动设置 |
| `API_BASE` | `https://api.siliconflow.cn/v1` | 硅基流动API地址 |
| `REQUIRE_AUTH` | `true` | 是否要求认证 |
| `AUTH_USERNAME` | `admin` | 基础认证用户名 |
| `AUTH_PASSWORD` | 空 | 基础认证密码 |
| `API_KEY` | 空 | API密钥认证密钥 |
| `USE_API_KEY_AUTH` | `false` | 是否使用API密钥认证 |
| `ENCRYPT_ENABLED` | `true` | 是否加密存储密钥 |
| `USE_ENV_STORAGE` | `false` | 是否使用环境变量存储密钥数据 |
| `ENCRYPTION_KEY` | 自动生成 | 加密密钥 |

## 注意事项

1. **Render免费套餐限制**:
   - 每月750小时免费时间（约31天）
   - 15分钟不活动后自动休眠
   - 冷启动需要约30秒
   - 适合低流量使用

2. **数据持久性**:
   - Render免费版重启会丢失本地文件
   - 建议: 定期导出备份 `GET /api/export_backup`
   - 或: 设置 `USE_ENV_STORAGE=true` 并将密钥数据存为环境变量

3. **安全性建议**:
   - 务必设置强密码或API密钥
   - 定期更换认证凭据
   - 启用密钥加密存储
   - 限制可访问的IP地址（Render付费功能）

4. **性能优化**:
   - 保持密钥数量合理（建议5-10个）
   - 定期检查密钥余额和健康状态
   - 移除无效或余额不足的密钥

## API端点

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/` | GET | 可选 | 管理界面 |
| `/v1/<path:path>` | 所有 | 可选 | 代理到API服务器 |
| `/api/data` | GET/POST | 是 | 密钥管理 |
| `/api/check_balance` | POST | 是 | 检查密钥余额 |
| `/api/export_backup` | GET | 是 | 导出备份 |
| `/api/import_backup` | POST | 是 | 导入备份 |
| `/api/export_keys_text` | GET | 是 | 导出密钥明文 |
| `/api/health` | GET | 否 | 健康检查 |

## 故障排除

### 1. 服务无法启动
- 检查requirements.txt是否正确
- 查看Render的构建日志
- 确认Python版本兼容性

### 2. 认证失败
- 确认设置了正确的环境变量
- 检查请求头格式
- 确认密码正确

### 3. 代理请求失败
- 检查API密钥是否有效
- 确认硅基流动API是否可达
- 查看应用日志获取详细信息

### 4. 数据丢失
- Render重启会导致本地文件丢失
- 定期备份数据
- 考虑使用环境变量存储关键数据

## 更新与维护

1. **更新代码**:
   - 在GitHub更新代码
   - Render会自动重新部署

2. **查看日志**:
   - 在Render仪表板的 "Logs" 标签页查看

3. **监控使用情况**:
   - 定期检查密钥余额
   - 监控服务响应时间
   - 查看错误日志

## 技术支持

如有问题，请:
1. 查看Render构建和运行日志
2. 检查环境变量设置
3. 确认网络连接正常
4. 查看本项目的GitHub Issues

---

**注意**: 免费服务有使用限制，如需高可用性请考虑升级到Render付费计划。