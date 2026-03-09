# Twitter 下载器 GUI

基于 [caolvchong-top/twitter_download](https://github.com/caolvchong-top/twitter_download) 开发的图形界面版本。

## 功能特点

- 图形化界面，无需修改配置文件
- **无需安装 Python 环境，依赖已内置**
- 用户管理：添加、删除要下载的用户
- 实时日志输出
- 一键下载整个用户列表
- 完整的设置选项（Cookie、保存路径、代理等）

## 使用方法

1. 下载 `TwitterDownloader.exe`
2. 双击运行
3. 添加要下载的用户
4. 在设置中填入 Cookie
5. 点击开始下载

## 配置说明

在设置界面中可以配置：
- **Cookie**: 登录 Twitter 后获取的 auth_token 和 ct0
- **保存路径**: 下载文件的保存位置
- **代理**: 如需代理访问
- 其他选项...

## 技术说明

- 使用 PyInstaller 打包
- 依赖已内置，无需安装 Python 环境
- 打包包含：httpx、XClientTransaction 等

## 许可证

MIT License - 基于原始项目 [twitter_download](https://github.com/caolvchong-top/twitter_download)

## 打包命令（开发者）

```bash
pyinstaller --onefile --windowed --name TwitterDownloader --add-data twitter_download-main;twitter_download-main --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.scrolledtext --collect-all httpx --collect-all XClientTransaction --collect-all httpcore --collect-all anyio --collect-all beautifulsoup4 gui.py
```
