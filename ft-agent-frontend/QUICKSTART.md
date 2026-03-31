# 快速启动指南

## 第一步：安装依赖

```bash
cd universal-agent-frontend
npm install
```

**注意**：如果安装速度慢，可以使用国内镜像：

```bash
# 使用淘宝镜像
npm install --registry=https://registry.npmmirror.com
```

## 第二步：确保后端服务运行

前端需要连接后端 API，请确保后端服务已启动：

```bash
# 在后端项目目录
cd universal-agent-backend
python main.py
```

后端服务应运行在 `http://localhost:8000`

## 第三步：启动前端开发服务器

```bash
npm run dev
```

看到以下输出表示成功：

```
  VITE v5.0.0  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

## 第四步：访问应用

打开浏览器访问：http://localhost:3000

## 使用流程

### 1. 注册账号

- 点击"注册"标签
- 填写用户名、昵称、密码
- 点击"注册"按钮

### 2. 开始对话

- 注册成功后自动进入聊天页面
- 在输入框输入消息
- 点击"发送"或按 `Ctrl+Enter`
- AI 助手会回复你的消息

### 3. 管理记忆

- 点击左侧"我的记忆"菜单
- 点击"添加记忆"按钮
- 选择记忆类型（个人信息/偏好/习惯）
- 填写记忆内容
- 保存后，AI 会在对话中考虑这些信息

### 4. 查看历史

- 点击"历史记录"菜单
- 可以按助手类型筛选
- 可以设置显示条数
- 可以清空历史记录

### 5. 个人中心

- 点击"个人中心"菜单
- 查看个人信息和统计数据
- 可以编辑昵称和邮箱

## 常见问题

### 1. 页面显示空白

**原因**：后端服务未启动

**解决**：
```bash
cd universal-agent-backend
python main.py
```

### 2. 登录失败

**原因**：
- 用户名或密码错误
- 后端服务未运行
- 数据库未初始化

**解决**：
- 检查输入的用户名密码
- 确保后端服务运行正常
- 重新注册账号

### 3. 发送消息无响应

**原因**：
- API key 未配置
- 后端 Agent 未配置
- 网络问题

**解决**：
- 检查后端 `.env` 中的 `OPENAI_API_KEY`
- 确保已设置 Agent（参考后端文档）
- 查看浏览器控制台错误信息

### 4. 样式显示异常

**原因**：依赖未正确安装

**解决**：
```bash
rm -rf node_modules package-lock.json
npm install
```

## 开发技巧

### 1. 热更新

代码修改后会自动刷新，无需手动重启

### 2. 查看网络请求

打开浏览器开发者工具（F12）→ Network 标签，可以查看所有 API 请求

### 3. 调试状态

使用 Vue DevTools 浏览器插件：
- Chrome: https://chrome.google.com/webstore/detail/vuejs-devtools/
- Firefox: https://addons.mozilla.org/zh-CN/firefox/addon/vue-js-devtools/

### 4. 清除缓存

如果遇到奇怪的问题，尝试清除浏览器缓存：
- Chrome: `Ctrl+Shift+Delete`
- Firefox: `Ctrl+Shift+Delete`

## 下一步

- 探索所有功能
- 尝试添加不同类型的记忆
- 体验多轮对话
- 查看个人数据统计

## 获取帮助

- 查看 [README.md](./README.md) 了解详细文档
- 检查后端项目文档
- 提交 Issue

祝使用愉快！🎉
