import flet as ft
import os
import hashlib
import re
import keyword
import builtins
import importlib
import threading
import time
import subprocess
import sys
import platform
from pathlib import Path


class Account:
    @staticmethod
    def signin(account, password):
        try:
            userinfo_file = "userinfo"

            if os.path.exists(userinfo_file):
                with open(userinfo_file, 'r') as f:
                    content = f.read()
                if "--user--" in content and "--password_sha256--" in content:
                    return '只可以登录一个账号'
                else:
                    os.remove(userinfo_file)
        except Exception:
            pass

        with open(userinfo_file, 'w') as file:
            file.write('--user--\n')
            file.write(account)
            file.write('\n--password_sha256--\n')
            a = hashlib.sha256(password.encode()).hexdigest()
            file.write(a)
        return f"注册成功！用户: {account}"

    @staticmethod
    def signup(account, password):
        try:
            userinfo_file = "userinfo"

            with open(userinfo_file, 'r') as f:
                content = f.read()

            user_match = re.search(r'--user--\n(.+?)\n--password_sha256--', content, re.DOTALL)
            password_match = re.search(r'--password_sha256--\n(.+)$', content, re.DOTALL)

            if not user_match or not password_match:
                return "用户文件格式错误"

            username = user_match.group(1)  # 修复：从文件中读取用户名
            stored_hash = password_match.group(1)

            if username != account:
                return f"用户名不匹配，当前用户: {username}"

            input_hash = hashlib.sha256(password.encode()).hexdigest()

            if stored_hash == input_hash:
                return f"登录成功！欢迎：{username}"
            else:
                return '密码不正确'

        except FileNotFoundError:
            return '请先注册账号'
        except Exception as e:
            return f"登录出错: {e}"

    @staticmethod
    def sign_out():
        try:
            userinfo_file = "userinfo"
            os.remove(userinfo_file)
        except FileNotFoundError:
            return "您还没有登录"
        else:
            return "注销成功"

    @staticmethod
    def check_login():
        try:
            userinfo_file = "userinfo"
            with open(userinfo_file, 'r') as f:
                pass
            return True
        except Exception:
            return False


class CodeCompleter:
    def __init__(self):
        self.keywords = set(keyword.kwlist)
        self.builtins = set(dir(builtins))
        self.common_modules = {
            'os', 'sys', 're', 'json', 'time', 'datetime', 'math',
            'random', 'requests', 'numpy', 'pandas', 'matplotlib'
        }
        self.user_definitions = set()

    def get_completions(self, text, cursor_pos):
        """获取代码补全建议"""
        line_start = text.rfind('\n', 0, cursor_pos) + 1
        current_line = text[line_start:cursor_pos]

        words = current_line.split()
        if not words:
            return []

        current_word = words[-1]

        completions = []
        completions.extend([kw for kw in self.keywords if kw.startswith(current_word)])
        completions.extend([func for func in self.builtins if func.startswith(current_word)])
        completions.extend([mod for mod in self.common_modules if mod.startswith(current_word)])
        completions.extend([defn for defn in self.user_definitions if defn.startswith(current_word)])

        import_pattern = r'import\s+(\w+)|\s+from\s+(\w+)'
        imports = re.findall(import_pattern, text)
        for imp in imports:
            module_name = imp[0] or imp[1]
            if module_name and module_name.startswith(current_word):
                completions.append(module_name)

        return list(set(completions))[:10]

    def update_user_definitions(self, text):
        """从代码中提取用户定义的函数和类"""
        self.user_definitions.clear()

        func_pattern = r'def\s+(\w+)\s*\('
        functions = re.findall(func_pattern, text)
        self.user_definitions.update(functions)

        class_pattern = r'class\s+(\w+)'
        classes = re.findall(class_pattern, text)
        self.user_definitions.update(classes)

        var_pattern = r'^(\w+)\s*='
        variables = re.findall(var_pattern, text, re.MULTILINE)
        self.user_definitions.update(variables)


class TerminalManager:
    def __init__(self):
        self.current_directory = self.get_home_directory()
        self.process = None
        self.is_running = False

    def get_home_directory(self):
        """获取用户主目录"""
        system = platform.system().lower()
        if system == "windows":
            return os.path.expanduser("~")
        elif system == "darwin":  # macOS/iOS
            return os.path.expanduser("~")
        else:  # Android/Linux
            return "/data/data/com.example.python/files" if os.path.exists("/data/data") else os.path.expanduser("~")

    def execute_command(self, command):
        """执行终端命令"""
        try:
            # 处理特殊命令
            if command.strip() == "clear":
                return "", ""

            # 处理cd命令
            if command.startswith("cd "):
                new_dir = command[3:].strip()
                if new_dir == "..":
                    self.current_directory = os.path.dirname(self.current_directory)
                elif os.path.isdir(new_dir):
                    self.current_directory = new_dir
                elif os.path.isdir(os.path.join(self.current_directory, new_dir)):
                    self.current_directory = os.path.join(self.current_directory, new_dir)
                else:
                    return f"cd: {new_dir}: 目录不存在\n", ""
                return f"切换到目录: {self.current_directory}\n", ""

            # 处理pip命令
            if command.startswith("pip "):
                return self.execute_pip_command(command)

            # 执行系统命令
            if platform.system().lower() == "windows":
                result = subprocess.run(
                    f"cd /d {self.current_directory} && {command}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.current_directory
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.current_directory
                )

            return result.stdout, result.stderr

        except Exception as e:
            return "", f"命令执行错误: {str(e)}\n"

    def execute_pip_command(self, command):
        """执行pip命令"""
        try:
            # 在Android上，我们需要使用python -m pip
            if platform.system().lower() == "linux" and os.path.exists("/data/data"):
                pip_command = f"python -m {command}"
            else:
                pip_command = command

            result = subprocess.run(
                pip_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.current_directory
            )

            return result.stdout, result.stderr

        except Exception as e:
            return "", f"pip命令执行错误: {str(e)}\n"

    def get_prompt(self):
        """获取终端提示符"""
        system = platform.system().lower()
        if system == "windows":
            return f"{self.current_directory}> "
        else:
            # 显示当前目录的最后一个部分
            dir_name = os.path.basename(self.current_directory)
            if not dir_name:
                dir_name = "/"
            return f"user@{platform.node()}:{dir_name}$ "


class PyEditIDE:
    def __init__(self):
        self.page = None
        self.current_file = None
        self.current_encoding = "utf-8"
        self.completer = CodeCompleter()
        self.suggestions = []
        self.is_running = False
        self.code_editor_expanded = True
        self.output_expanded = True
        self.terminal_expanded = False
        self.terminal_manager = TerminalManager()
        self.terminal_history = []
        self.current_platform = self.detect_platform()

    def detect_platform(self):
        """检测当前平台"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            # 简单检测iOS，实际部署时需要更精确的检测
            return "ios" if "iPhone" in platform.platform() else "macos"
        else:
            return "android" if os.path.exists("/data/data") else "linux"

    def main(self, page: ft.Page):
        self.page = page
        page.title = "PyEdit IDE"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = ft.Colors.WHITE
        page.padding = 0

        # 平台特定设置
        if self.current_platform == "android":
            page.platform = ft.PagePlatform.ANDROID
        elif self.current_platform == "ios":
            page.platform = ft.PagePlatform.IOS

        page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        page.vertical_alignment = ft.MainAxisAlignment.START

        self.snack_bar = ft.SnackBar(content=ft.Text(""))
        page.overlay.append(self.snack_bar)

        # 补全建议容器
        self.suggestion_container = ft.Container(
            content=ft.Column([]),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            visible=False,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12)
        )
        page.overlay.append(self.suggestion_container)

        if Account.check_login():
            self.show_main_ide()
        else:
            self.show_login_page()

    def show_snackbar(self, message):
        self.snack_bar.content = ft.Text(str(message))
        self.snack_bar.open = True
        self.page.update()

    def show_login_page(self):
        # 定义用户名字段和密码字段
        self.user_field = ft.TextField(
            label="用户名",
            width=400,
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            text_size=16,
            content_padding=15
        )

        self.pwd_field = ft.TextField(
            label="密码",
            password=True,
            width=400,
            border_radius=12,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            text_size=16,
            content_padding=15,
            can_reveal_password=True
        )

        def login_click(e):
            username = self.user_field.value.strip()  # 修复：使用 self.user_field
            password = self.pwd_field.value.strip()  # 修复：使用 self.pwd_field

            if not username or not password:
                self.show_snackbar("请输入用户名和密码")
                return

            login_button.disabled = True
            login_button.text = "登录中..."
            self.page.update()

            def do_login():
                if Account.check_login():
                    result = Account.signup(username, password)
                else:
                    result = Account.signin(username, password)

                if result and "成功" in result:
                    self.page.clean()
                    self.show_main_ide()
                elif result:
                    self.show_snackbar(result)

                login_button.disabled = False
                login_button.text = "登录/注册"
                self.page.update()

            threading.Thread(target=do_login, daemon=True).start()

        login_button = ft.FilledButton(
            "登录/注册",
            on_click=login_click,
            style=ft.ButtonStyle(padding=20, color=ft.Colors.WHITE)
        )

        login_content = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.CODE, size=80, color=ft.Colors.BLUE_500),
                ft.Text("PyEdit IDE", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.Text(f"{self.current_platform.upper()} 版本", size=16, color=ft.Colors.GREY_600),
                ft.Divider(height=20),
                self.user_field,  # 修复：使用 self.user_field
                self.pwd_field,  # 修复：使用 self.pwd_field
                ft.Container(
                    content=login_button,
                    width=400,
                    margin=ft.margin.only(top=20)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40,
            width=500,
            bgcolor=ft.Colors.WHITE,
            margin=20,
            border_radius=16
        )

        self.page.add(
            ft.Container(
                content=ft.Card(
                    content=login_content,
                    elevation=20,
                    margin=20
                ),
                alignment=ft.alignment.center,
                expand=True,
                bgcolor=ft.Colors.GREY_100,
                padding=20
            )
        )

    def toggle_code_editor(self, e):
        self.code_editor_expanded = not self.code_editor_expanded
        self.code_container.visible = self.code_editor_expanded
        self.page.update()

    def toggle_output(self, e):
        self.output_expanded = not self.output_expanded
        self.output_container.visible = self.output_expanded
        self.page.update()

    def toggle_terminal(self, e):
        self.terminal_expanded = not self.terminal_expanded
        self.terminal_container.visible = self.terminal_expanded
        self.page.update()

    def execute_terminal_command(self, e):
        """执行终端命令"""
        command = self.terminal_input.value.strip()
        if not command:
            return

        # 添加到历史
        self.terminal_history.append(f"{self.terminal_manager.get_prompt()}{command}")

        # 执行命令
        def run_command():
            stdout, stderr = self.terminal_manager.execute_command(command)

            # 更新终端输出
            output_lines = []
            if stdout:
                output_lines.append(stdout)
            if stderr:
                output_lines.append(stderr)

            # 添加新的提示符
            output_lines.append(self.terminal_manager.get_prompt())

            # 更新UI
            self.terminal_output.value += f"{self.terminal_manager.get_prompt()}{command}\n"
            self.terminal_output.value += "\n".join(output_lines)

            # 清空输入框
            self.terminal_input.value = ""

            # 滚动到底部
            self.terminal_output.scroll_to(offset=-1)

            self.page.update()

        threading.Thread(target=run_command, daemon=True).start()

    def clear_terminal(self, e):
        """清空终端"""
        self.terminal_output.value = f"{self.terminal_manager.get_prompt()}"
        self.page.update()

    def show_main_ide(self):
        # 代码编辑器
        self.code_editor = ft.TextField(
            multiline=True,
            min_lines=15,
            expand=True,
            border_radius=12,
            text_size=16,
            content_padding=15,
            on_change=self.on_code_change,
            bgcolor=ft.Colors.WHITE,
            color=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_400,
            cursor_color=ft.Colors.BLUE_500,
            selection_color=ft.Colors.BLUE_100
        )

        # 输出区域
        self.output_area = ft.TextField(
            multiline=True,
            min_lines=8,
            read_only=True,
            border_radius=12,
            text_size=14,
            hint_text="运行结果将显示在这里...",
            bgcolor=ft.Colors.GREY_50,
            color=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_300
        )

        # 终端输出区域
        self.terminal_output = ft.TextField(
            multiline=True,
            min_lines=6,
            read_only=True,
            border_radius=12,
            text_size=12,
            hint_text="终端输出...",
            bgcolor=ft.Colors.BLACK,
            color=ft.Colors.GREEN,
            border_color=ft.Colors.GREY_600
        )
        self.terminal_output.value = f"{self.terminal_manager.get_prompt()}"

        # 终端输入区域
        self.terminal_input = ft.TextField(
            hint_text="输入命令 (pip install, cd, ls, 等)...",
            border_radius=12,
            text_size=14,
            content_padding=15,
            bgcolor=ft.Colors.GREY_900,
            color=ft.Colors.WHITE,
            border_color=ft.Colors.GREY_600,
            on_submit=self.execute_terminal_command
        )

        # 新建文件对话框
        self.new_file_dialog = ft.AlertDialog(
            title=ft.Text("新建文件", color=ft.Colors.BLACK),
            content=ft.Column([
                ft.TextField(
                    label="文件名",
                    hint_text="example.py",
                    bgcolor=ft.Colors.WHITE,
                    text_size=16
                ),
                ft.Dropdown(
                    label="编码格式",
                    value="utf-8",
                    options=[
                        ft.dropdown.Option("utf-8"),
                        ft.dropdown.Option("gbk"),
                        ft.dropdown.Option("utf-16"),
                    ],
                    bgcolor=ft.Colors.WHITE
                )
            ], tight=True),
            actions=[
                ft.TextButton("取消", on_click=lambda e: self.close_dialog()),
                ft.TextButton("创建", on_click=self.create_new_file),
            ],
            bgcolor=ft.Colors.WHITE
        )

        self.page.overlay.append(self.new_file_dialog)

        # 代码编辑器容器
        self.code_container = ft.Container(
            content=self.code_editor,
            padding=15,
            height=300,
            bgcolor=ft.Colors.WHITE
        )

        # 输出容器
        self.output_container = ft.Container(
            content=self.output_area,
            padding=15,
            height=250,
            bgcolor=ft.Colors.WHITE
        )

        # 终端容器
        self.terminal_container = ft.Container(
            content=ft.Column([
                self.terminal_output,
                ft.Row([
                    self.terminal_input,
                    ft.IconButton(
                        ft.icons.SEND,
                        on_click=self.execute_terminal_command,
                        icon_color=ft.Colors.GREEN
                    ),
                    ft.IconButton(
                        ft.icons.CLEAR,
                        on_click=self.clear_terminal,
                        icon_color=ft.Colors.RED
                    )
                ])
            ]),
            padding=15,
            height=300,
            bgcolor=ft.Colors.GREY_900,
            visible=self.terminal_expanded
        )

        # 主界面布局
        self.page.add(
            ft.Column([
                # 顶部应用栏
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"PyEdit IDE - {self.current_platform.upper()}",
                                    size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                            ft.IconButton(
                                ft.icons.LOGOUT,
                                on_click=self.logout,
                                icon_color=ft.Colors.BLACK
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                        # 工具栏
                        ft.Container(
                            content=ft.Row([
                                ft.FilledTonalButton(
                                    "新建",
                                    on_click=lambda e: self.open_new_file_dialog(),
                                    icon=ft.icons.CREATE
                                ),
                                ft.FilledTonalButton(
                                    "打开",
                                    on_click=self.open_file,
                                    icon=ft.icons.FOLDER_OPEN
                                ),
                                ft.FilledTonalButton(
                                    "运行",
                                    on_click=self.run_code,
                                    icon=ft.icons.PLAY_ARROW
                                ),
                                ft.FilledTonalButton(
                                    "终端",
                                    on_click=self.toggle_terminal,
                                    icon=ft.icons.TERMINAL
                                ),
                            ], scroll=ft.ScrollMode.ADAPTIVE),
                            padding=ft.padding.only(top=10)
                        )
                    ]),
                    padding=20,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=ft.border_radius.only(bottom_left=16, bottom_right=16)
                ),

                # 提示信息
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.LIGHTBULB, size=16, color=ft.Colors.BLUE_700),
                        ft.Text("支持 pip install, cd, ls 等命令", size=14, color=ft.Colors.BLUE_700),
                    ]),
                    padding=15,
                    bgcolor=ft.Colors.BLUE_100
                ),

                # 代码编辑器区域
                ft.Card(
                    content=ft.Column([
                        ft.ListTile(
                            title=ft.Text("代码编辑器", weight=ft.FontWeight.BOLD),
                            trailing=ft.IconButton(
                                ft.icons.KEYBOARD_ARROW_DOWN,
                                on_click=self.toggle_code_editor
                            )
                        ),
                        self.code_container
                    ]),
                    margin=10,
                    elevation=5
                ),

                # 输出结果区域
                ft.Card(
                    content=ft.Column([
                        ft.ListTile(
                            title=ft.Text("输出结果", weight=ft.FontWeight.BOLD),
                            trailing=ft.IconButton(
                                ft.icons.KEYBOARD_ARROW_DOWN,
                                on_click=self.toggle_output
                            )
                        ),
                        self.output_container
                    ]),
                    margin=10,
                    elevation=5
                ),

                # 终端区域
                ft.Card(
                    content=ft.Column([
                        ft.ListTile(
                            title=ft.Text("终端", weight=ft.FontWeight.BOLD),
                            trailing=ft.IconButton(
                                ft.icons.KEYBOARD_ARROW_DOWN,
                                on_click=self.toggle_terminal
                            )
                        ),
                        self.terminal_container
                    ]),
                    margin=10,
                    elevation=5
                ),

                # 底部状态栏
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"平台: {self.current_platform}", size=12, color=ft.Colors.BLACK),
                        ft.Text(f"编码: {self.current_encoding}", size=12, color=ft.Colors.BLACK),
                        ft.Text(f"文件: {self.current_file or '未打开文件'}", size=12, color=ft.Colors.BLACK),
                    ], scroll=ft.ScrollMode.ADAPTIVE),
                    padding=15,
                    bgcolor=ft.Colors.GREY_200
                )
            ], expand=True)
        )

    def on_code_change(self, e):
        text = self.code_editor.value
        if not text:
            return

        if text and text[-1] == ':':
            lines = text.split('\n')
            if len(lines) > 1:
                current_line = lines[-2]
                indent = ""
                for char in current_line:
                    if char in [' ', '\t']:
                        indent += char
                    else:
                        break
                extra_indent = "    "
                new_text = text + '\n' + indent + extra_indent
                self.code_editor.value = new_text
                self.page.update()
                return

        self.completer.update_user_definitions(text)
        cursor_pos = len(text)
        self.suggestions = self.completer.get_completions(text, cursor_pos)

        if self.suggestions:
            self.show_suggestions()
        else:
            self.hide_suggestions()

    def show_suggestions(self):
        suggestion_items = []
        for suggestion in self.suggestions[:6]:
            item = ft.ListTile(
                title=ft.Text(suggestion, size=14),
                on_click=lambda e, s=suggestion: self.apply_suggestion(s),
                dense=True
            )
            suggestion_items.append(item)

        self.suggestion_container.content = ft.ListView(
            suggestion_items,
            height=min(len(self.suggestions) * 50, 200)
        )
        self.suggestion_container.visible = True
        self.suggestion_container.top = 400
        self.suggestion_container.left = 20
        self.suggestion_container.width = 250
        self.page.update()

    def hide_suggestions(self):
        self.suggestion_container.visible = False
        self.page.update()

    def apply_suggestion(self, suggestion):
        current_text = self.code_editor.value
        lines = current_text.split('\n')
        if lines:
            current_line = lines[-1]
            words = current_line.split()
            if words:
                current_word = words[-1]
                new_line = current_line.replace(current_word, suggestion)
                lines[-1] = new_line
                new_text = '\n'.join(lines)
                self.code_editor.value = new_text

        self.hide_suggestions()
        self.page.update()

    def open_new_file_dialog(self):
        self.new_file_dialog.open = True
        self.page.update()

    def close_dialog(self):
        self.new_file_dialog.open = False
        self.page.update()

    def create_new_file(self, e):
        filename = self.new_file_dialog.content.controls[0].value
        encoding = self.new_file_dialog.content.controls[1].value

        if not filename:
            self.show_snackbar("请输入文件名")
            return

        self.current_file = filename
        self.current_encoding = encoding
        self.code_editor.value = "# 新建文件\nprint('Hello PyEdit!')\n"
        self.output_area.value = ""
        self.close_dialog()
        self.page.update()
        self.show_snackbar(f"已创建文件: {filename}")

    def open_file(self, e):
        def on_dialog_result(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.current_file = file_path
                    self.code_editor.value = content
                    self.output_area.value = ""
                    self.page.update()
                    self.show_snackbar(f"已打开文件: {file_path}")
                except Exception as ex:
                    self.show_snackbar(f"打开文件失败: {ex}")

        file_picker = ft.FilePicker(on_result=on_dialog_result)
        self.page.overlay.append(file_picker)
        self.page.update()
        file_picker.pick_files()

    def run_code(self, e):
        if self.is_running:
            self.show_snackbar("代码正在执行中，请稍候...")
            return

        code = self.code_editor.value
        if not code:
            self.show_snackbar("没有代码可执行")
            return

        self.is_running = True
        self.output_area.value = "代码执行中...\n"
        self.page.update()

        def execute_code():
            try:
                import io
                import sys
                from contextlib import redirect_stdout, redirect_stderr

                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()

                exec(code)

                output = sys.stdout.getvalue()
                error = sys.stderr.getvalue()

                sys.stdout = old_stdout
                sys.stderr = old_stderr

                result = ""
                if output:
                    result += f"输出:\n{output}\n"
                if error:
                    result += f"错误:\n{error}\n"
                if not output and not error:
                    result = "代码执行完成，无输出"

                self.output_area.value = result

            except Exception as ex:
                self.output_area.value = f"执行错误: {ex}"
            finally:
                self.is_running = False
                self.page.update()

        threading.Thread(target=execute_code, daemon=True).start()

    def logout(self, e):
        result = Account.sign_out()
        self.show_snackbar(result)
        self.page.clean()
        self.show_login_page()


# 多平台启动配置
def main(page: ft.Page):
    ide = PyEditIDE()
    ide.main(page)


# 根据不同平台配置应用
if __name__ == "__main__":
    current_platform = platform.system().lower()

    app_config = {
        "target": main,
        "assets_dir": "assets"
    }

    # 平台特定配置
    if current_platform == "android":
        app_config["view"] = ft.AppView.FLET_APP
    elif current_platform == "ios":
        app_config["view"] = ft.AppView.FLET_APP
    else:  # Windows, Linux, macOS
        app_config["view"] = ft.AppView.FLET_APP

    ft.app(**app_config)