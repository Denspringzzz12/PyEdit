# PyEdit IDE - 跨平台 Python IDE

一个完全开源的跨平台 Python IDE，基于 Flet 框架开发，支持 Android、iOS 和 Windows。

## ✨ 特性

### 🖥️ 代码编辑
- **代码补全（智能）** - 补全 Python 关键字、内置函数、自定义标识符
- **语法高亮** - 自动缩进、格式化代码
- **自动换行** - 按冒号自动补全下一行缩进

### 🚀 代码执行
- **实时代码执行** - 一体化环境下的 Python 代码快速执行
- **执行输出** - 清晰可见的执行结果、执行错误信息
- **多线程执行** - 避免界面卡顿

### 🔧 代码控制台
- **完整终端** - 包含常用 Linux 或 Windows 命令
- **Pip 执行** - 支持 `pip install`、`pip list` 等命令
- **文件操作** - 支持 `cd`、`ls`、`pwd` 等文件操作命令
- **命令记录执行** - 历史命令记录及执行

### 🔐 用户系统
- **用户注册/用户登录** - 安全和授权的用户系统
- **加密密码** - 使用 SHA-256 加密处理
- **Session 自动登录、注销** - 用户会话管理

### 📱 多平台支持
- **安卓 APK** - 完整的移动设备应用程序实现
- **iOS 支持** - 支持苹果设备
- **Windows** - 支持 Windows 桌面环境

## 🛠️ 技术栈

- **前端框架**: Flet
- **编程语言**: Python
- **平台支持**: Android, iOS, Windows

## 📦 安装

```bash
# 克隆项目
git clone https://github.com/Denspringzzz12/PyEdit

# 安装依赖
pip install flet

# 运行应用
python main.py
