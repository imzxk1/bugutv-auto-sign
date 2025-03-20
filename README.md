# BuguTV 自动签到

这是一个用于自动登录并签到 [BuguTV](https://www.bugutv.vip) 网站的工具。支持定时执行、错误重试和邮件通知功能。

## 功能特点

- 全自动登录和签到，无需人工干预
- 自动重试机制，应对临时性错误
- 详细的日志记录
- 支持邮件通知签到结果
- 通过GitHub Actions实现云端定时执行

## 运行环境要求

- Python 3.8+
- 以下Python库：
  - requests
  - python-dotenv

## 本地运行说明

1. 克隆本仓库到本地：

```bash
git clone [你的仓库URL]
cd bugutv-auto-sign
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 复制`.env.example`为`.env`，并填入您的账号信息：

```bash
cp .env.example .env
```

4. 编辑`.env`文件，填入您的登录信息和邮件通知配置（可选）

5. 运行脚本：

```bash
python autosign.py
```

## 云端部署（GitHub Actions）

1. Fork本仓库到您的GitHub账号下

2. 在您的仓库中添加以下Secrets（设置 -> Secrets and variables -> Actions -> New repository secret）：
   - `BUGUTV_USERNAME`: 您的BuguTV登录邮箱
   - `BUGUTV_PASSWORD`: 您的BuguTV登录密码
   - （可选）`EMAIL_HOST`: SMTP服务器
   - （可选）`EMAIL_PORT`: SMTP端口
   - （可选）`EMAIL_USERNAME`: SMTP用户名
   - （可选）`EMAIL_PASSWORD`: SMTP密码
   - （可选）`EMAIL_TO`: 通知接收邮箱

3. GitHub Actions将会按照配置的时间自动运行（默认每天北京时间早上8点）

4. 您也可以在Actions标签页手动触发工作流程

## 安全性说明

- 所有敏感信息通过环境变量或GitHub Secrets存储，不会暴露在代码中
- 本地运行时，敏感信息保存在`.env`文件中，请确保该文件不被提交到版本控制系统
- GitHub Actions运行时使用GitHub Secrets安全存储敏感信息

## 日志

- 日志文件保存在`logs`目录下
- 在GitHub Actions运行时，日志会被保存为构建产物，可以下载查看

## 实现原理

本脚本使用Python的requests库模拟网页请求，实现自动登录和签到功能，无需使用浏览器。主要流程如下：

1. 请求网站首页获取cookies
2. 请求登录页面
3. 执行AJAX登录请求
4. 验证登录状态并获取签到所需的nonce值
5. 执行签到请求
6. 解析签到结果并记录日志

## 注意事项

- 请遵守网站的使用条款和规则
- 如网站更新导致脚本失效，请提交issue或自行更新代码
- 建议不要频繁运行脚本，以避免被网站限制访问

## 许可证

MIT 