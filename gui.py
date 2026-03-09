# -*- coding: utf-8 -*-
"""
Twitter 下载器 GUI
依赖: tkinter (内置), requests, httpx
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import os
import subprocess
import threading
import sys
import shutil

# 路径配置
import tempfile
import shutil

if getattr(sys, 'frozen', False):
    # 打包后运行
    BASE_DIR = os.path.dirname(sys.executable)
    # 如果 twitter_download-main 不存在，从临时目录复制
    TWITTER_DOWNLOAD_DIR = os.path.join(BASE_DIR, "twitter_download-main")
    if not os.path.exists(TWITTER_DOWNLOAD_DIR):
        # 从临时目录复制（PyInstaller 解压的资源）
        temp_dir = sys._MEIPASS
        src_dir = os.path.join(temp_dir, "twitter_download-main")
        if os.path.exists(src_dir):
            shutil.copytree(src_dir, TWITTER_DOWNLOAD_DIR)
        else:
            # 如果不存在，创建空目录
            os.makedirs(TWITTER_DOWNLOAD_DIR, exist_ok=True)
else:
    # 开发时运行
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TWITTER_DOWNLOAD_DIR = os.path.join(BASE_DIR, "twitter_download-main")

SETTINGS_FILE = os.path.join(TWITTER_DOWNLOAD_DIR, "settings.json")
ACCOUNTS_FILE = os.path.join(TWITTER_DOWNLOAD_DIR, "accounts.txt")
DEFAULT_SAVE_PATH = os.path.join(os.path.expanduser("~"), "Pictures")

# 配置项定义（用于设置界面）
CONFIG_ITEMS = [
    ("cookie", "Cookie", "str"),
    ("save_path", "保存路径", "file"),
    ("user_lst", "用户列表(备用)", "str"),
    ("has_retweet", "包含转推", "bool"),
    ("high_lights", "亮点(Highlights)", "bool"),
    ("likes", "喜欢(Likes)", "bool"),
    ("time_range", "时间范围", "str"),
    ("down_log", "记录已下载", "bool"),
    ("autoSync", "自动同步最新", "bool"),
    ("image_format", "图片格式", "combo", ["orig", "jpg", "png"]),
    ("has_video", "下载视频", "bool"),
    ("log_output", "输出日志", "bool"),
    ("max_concurrent_requests", "最大并发数", "int"),
    ("proxy", "代理", "str"),
    ("md_output", "Markdown输出", "bool"),
    ("media_count_limit", "媒体数量限制", "int"),
]


class TwitterDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Twitter 下载器")
        self.root.geometry("900x600")
        
        self.settings = {}
        self.user_list = []  # 当前用户列表
        self.download_process = None
        self.is_downloading = False
        self.download_btn = None
        
        self.load_settings()
        self.create_ui()
    
    def load_settings(self):
        """加载配置"""
        # 确保目录存在
        os.makedirs(TWITTER_DOWNLOAD_DIR, exist_ok=True)
        
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                self.settings = json.load(f)
            # 调试日志
            print(f"已加载配置: {SETTINGS_FILE}")
            print(f"用户列表: {self.settings.get('user_lst', '')}")
        else:
            # 创建默认配置
            self.settings = {
                "save_path": DEFAULT_SAVE_PATH,
                "user_lst": "",
                "cookie": "",
                "has_retweet": False,
                "high_lights": False,
                "likes": False,
                "time_range": "1990-01-01:2030-01-01",
                "down_log": True,
                "autoSync": True,
                "image_format": "orig",
                "has_video": True,
                "log_output": True,
                "max_concurrent_requests": 8,
                "proxy": "",
                "md_output": True,
                "media_count_limit": 0,
            }
            print(f"使用默认配置，路径: {SETTINGS_FILE}")
        
        # 获取用户列表
        user_lst = self.settings.get("user_lst", "")
        self.user_list = [u.strip() for u in user_lst.split(",") if u.strip()]
        print(f"解析后的用户列表: {self.user_list}")
    
    def save_settings(self):
        """保存配置"""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            self.log("配置已保存到: " + SETTINGS_FILE)
        except Exception as e:
            self.log("保存配置失败: " + str(e))
    
    def create_ui(self):
        """创建界面"""
        # 顶部标题栏
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(title_frame, text="Twitter 下载器", font=("微软雅黑", 14, "bold")).pack(side="left")
        ttk.Button(title_frame, text="⚙️ 设置", command=self.open_settings).pack(side="right")
        
        # 主内容区分隔
        separator = ttk.Separator(self.root, orient="horizontal")
        separator.pack(fill="x", pady=5)
        
        # 中间内容区（用户列表 + 下载控制）
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧：用户列表
        left_frame = ttk.LabelFrame(content_frame, text="用户列表")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 用户列表框（多选）
        self.user_listbox = tk.Listbox(left_frame, selectmode="extended", height=10)
        self.user_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_user_listbox()
        
        # 用户操作按钮
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="+ 添加", command=self.add_user).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="- 删除", command=self.delete_user).pack(side="left", padx=2)
        
        # 右侧：下载控制
        right_frame = ttk.LabelFrame(content_frame, text="下载控制")
        right_frame.pack(side="right", fill="both", padx=(5, 0))
        
        control_frame = ttk.Frame(right_frame)
        control_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ttk.Button(control_frame, text="▶ 开始下载", command=self.start_download).pack(fill="x", pady=5)
        self.download_btn = ttk.Button(control_frame, text="⏹ 停止下载", command=self.stop_download)
        self.download_btn.pack(fill="x", pady=5)
        ttk.Button(control_frame, text="📂 打开下载位置", command=self.open_download_folder).pack(fill="x", pady=5)
        
        # 底部：日志输出
        log_frame = ttk.LabelFrame(self.root, text="日志输出")
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap="word", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def refresh_user_listbox(self):
        """刷新用户列表显示"""
        self.user_listbox.delete(0, tk.END)
        for user in self.user_list:
            self.user_listbox.insert(tk.END, user)
    
    def add_user(self):
        """添加用户"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加用户")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="用户名:").pack(pady=5)
        entry = ttk.Entry(dialog, width=30)
        entry.pack(pady=5)
        entry.focus()
        
        def confirm():
            username = entry.get().strip()
            if username:
                if username not in self.user_list:
                    self.user_list.append(username)
                    self.save_user_list()
                    self.refresh_user_listbox()
                dialog.destroy()
        
        ttk.Button(dialog, text="确定", command=confirm).pack(pady=5)
        entry.bind("<Return>", lambda e: confirm())
    
    def delete_user(self):
        """删除选中用户"""
        selected = self.user_listbox.curselection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的用户")
            return
        
        for i in reversed(selected):
            del self.user_list[i]
        self.save_user_list()
        self.refresh_user_listbox()
    
    def save_user_list(self):
        """保存用户列表到配置"""
        self.settings["user_lst"] = ",".join(self.user_list)
        self.save_settings()
    
    def open_settings(self):
        """打开设置窗口"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("550x700")
        dialog.transient(self.root)
        
        # 滚动区域
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建配置项控件
        self.config_widgets = {}
        
        for key, label, typ, *extra in CONFIG_ITEMS:
            frame = ttk.Frame(scrollable_frame, padding=5)
            frame.pack(fill="x")
            
            ttk.Label(frame, text=label, width=15).pack(side="left")
            
            value = self.settings.get(key, "")
            
            if typ == "bool":
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(frame, variable=var).pack(side="left")
                self.config_widgets[key] = ("bool", var)
            
            elif typ == "combo":
                var = tk.StringVar(value=value)
                ttk.Combobox(frame, textvariable=var, values=extra[0], width=30, state="readonly").pack(side="left")
                self.config_widgets[key] = ("combo", var)
            
            elif typ == "int":
                var = tk.IntVar(value=int(value) if value else 0)
                ttk.Entry(frame, textvariable=var, width=33).pack(side="left")
                self.config_widgets[key] = ("int", var)
            
            elif typ == "file":
                var = tk.StringVar(value=value)
                entry = ttk.Entry(frame, textvariable=var, width=25)
                entry.pack(side="left", padx=(0, 5))
                ttk.Button(frame, text="浏览", command=lambda v=var: self.browse_folder(v)).pack(side="left")
                self.config_widgets[key] = ("str", var)
            
            elif key == "cookie":
                # Cookie 字段使用更大的文本框
                var = tk.StringVar(value=value)
                text_widget = tk.Text(frame, height=9, width=45, wrap="word")
                text_widget.pack(side="left", padx=(0, 5))
                text_widget.insert("1.0", value)
                self.config_widgets[key] = ("text", text_widget, var)
            
            else:
                var = tk.StringVar(value=value)
                ttk.Entry(frame, textvariable=var, width=33).pack(side="left")
                self.config_widgets[key] = ("str", var)
        
        # 保存按钮
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="保存", command=lambda: self.save_settings_from_dialog(dialog)).pack()
    
    def browse_folder(self, var):
        """选择文件夹"""
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
    
    def save_settings_from_dialog(self, dialog):
        """从设置窗口保存配置"""
        for key, data in self.config_widgets.items():
            if data[0] == "bool":
                self.settings[key] = data[1].get()
            elif data[0] in ("int", "combo"):
                self.settings[key] = data[1].get()
            elif data[0] == "text":
                # Cookie 使用 Text 控件获取
                self.settings[key] = data[1].get("1.0", "end").strip()
            else:
                self.settings[key] = data[1].get()
        
        self.save_settings()
        dialog.destroy()
        messagebox.showinfo("提示", "设置已保存")
    
    def log(self, message):
        """输出日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def start_download(self):
        """开始下载"""
        # 直接下载整个用户列表
        if not self.user_list:
            self.log("用户列表为空，请先添加用户")
            return
        
        # 保存当前用户列表到配置
        self.settings["user_lst"] = ",".join(self.user_list)
        self.save_settings()
        
        self.is_downloading = True
        self.log("=" * 40)
        self.log(f"开始下载用户: {', '.join(self.user_list)}")
        
        # 禁用下载按钮
        self.download_btn.config(state="disabled")
        
        # 后台线程执行下载
        threading.Thread(target=self.run_download, daemon=True).start()
    
    def run_download(self):
        """执行下载（后台线程）- 直接导入运行脚本"""
        import sys
        import os
        import importlib.util
        
        # 添加下载脚本目录到 Python 路径
        download_dir = TWITTER_DOWNLOAD_DIR
        if download_dir not in sys.path:
            sys.path.insert(0, download_dir)
        
        self.log("开始下载...")
        
        # 创建自定义输出捕获
        class LogCapture:
            def __init__(self, callback):
                self.callback = callback
                self.buffer = ""
            
            def write(self, text):
                self.buffer += text
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    if line.strip():
                        self.callback(line)
            
            def flush(self):
                pass
        
        log_capture = LogCapture(lambda line: self.root.after(0, lambda l=line: self.log(l)))
        
        try:
            # 切换到下载目录
            old_cwd = os.getcwd()
            os.chdir(download_dir)
            
            # 动态加载 main.py
            main_py_path = os.path.join(download_dir, "main.py")
            spec = importlib.util.spec_from_file_location("main", main_py_path)
            main_module = importlib.util.module_from_spec(spec)
            
            # 替换 stdout 来捕获输出
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = log_capture
            sys.stderr = log_capture
            
            try:
                # 加载模块（不执行 if __name__ == '__main__'）
                spec.loader.exec_module(main_module)
                
                # 获取 User_info 类并为每个用户执行下载
                User_info = main_module.User_info
                user_list = self.settings.get("user_lst", "").split(",")
                
                for username in user_list:
                    username = username.strip()
                    if username:
                        self.root.after(0, lambda u=username: self.log(f"开始下载用户: {u}"))
                        user_info = User_info(username)
                        main_module.main(user_info)
                
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                os.chdir(old_cwd)
            
            self.root.after(0, lambda: self.log("下载完成"))
        
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.root.after(0, lambda: self.log(f"错误: {str(e)}"))
            self.root.after(0, lambda: self.log(error_msg))
        
        finally:
            self.is_downloading = False
            self.root.after(0, lambda: self.download_btn.config(state="normal"))
    
    def stop_download(self):
        """停止下载"""
        if self.is_downloading:
            self.is_downloading = False
            self.log("已停止下载")
    
    def open_download_folder(self):
        """打开下载目录"""
        save_path = self.settings.get("save_path", DEFAULT_SAVE_PATH)
        if os.path.exists(save_path):
            os.startfile(save_path)
        else:
            messagebox.showwarning("提示", f"目录不存在: {save_path}")


def main():
    root = tk.Tk()
    app = TwitterDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
