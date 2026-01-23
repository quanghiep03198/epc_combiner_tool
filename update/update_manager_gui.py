#!/usr/bin/env python3
"""
GUI Update Manager - Tkinter interface for EPC Update Manager
Converts the console application to a graphical user interface
"""

import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# Import the existing update manager logic
from update_manager import CleanUpdateManager, get_latest_release_info, SafeLogger


class UpdateManagerGUI:
    """GUI wrapper for the Update Manager"""

    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống Cập nhật Phần mềm")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Update manager instance
        self.update_manager = CleanUpdateManager()
        self.update_thread = None
        self.is_updating = False

        # Create GUI components
        self.create_widgets()

        # Redirect logger output to GUI
        self.setup_logger_redirect()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def create_widgets(self):
        """Create all GUI widgets"""

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title Label
        title_label = ttk.Label(
            main_frame,
            text="Hệ thống Cập nhật Phần mềm",
            font=("Arial", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        # Input fields section
        input_frame = ttk.LabelFrame(main_frame, text="Cấu hình cập nhật", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Update URL
        ttk.Label(input_frame, text="URL Cập nhật:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.url_entry = ttk.Entry(input_frame, width=50)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.url_entry.insert(0, "")
        ttk.Label(input_frame, text="(Để trống để tự động phát hiện)", font=("Arial", 8)).grid(
            row=1, column=1, columnspan=2, sticky=tk.W
        )

        # Install Directory
        ttk.Label(input_frame, text="Thư mục cài đặt:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.install_dir_entry = ttk.Entry(input_frame, width=40)
        self.install_dir_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.install_dir_entry.insert(0, ".")
        ttk.Button(input_frame, text="Chọn...", command=self.browse_install_dir).grid(
            row=2, column=2, padx=(5, 0), pady=5
        )

        # Current Version
        ttk.Label(input_frame, text="Phiên bản hiện tại:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        self.version_entry = ttk.Entry(input_frame, width=50)
        self.version_entry.grid(
            row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        self.version_entry.insert(0, "1.0.0")

        # Backup Directory
        ttk.Label(input_frame, text="Thư mục sao lưu:").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        self.backup_dir_entry = ttk.Entry(input_frame, width=40)
        self.backup_dir_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        self.backup_dir_entry.insert(0, "")
        ttk.Button(input_frame, text="Chọn...", command=self.browse_backup_dir).grid(
            row=4, column=2, padx=(5, 0), pady=5
        )

        # Process Names
        ttk.Label(input_frame, text="Tên tiến trình:").grid(
            row=5, column=0, sticky=tk.W, pady=5
        )
        self.process_entry = ttk.Entry(input_frame, width=50)
        self.process_entry.grid(
            row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        self.process_entry.insert(0, "main.exe")
        ttk.Label(input_frame, text="(Phân cách bằng dấu phẩy)", font=("Arial", 8)).grid(
            row=6, column=1, columnspan=2, sticky=tk.W
        )

        # Options checkboxes
        options_frame = ttk.LabelFrame(main_frame, text="Tùy chọn", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        self.force_var = tk.BooleanVar(value=False)
        self.silent_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(
            options_frame, text="Buộc cập nhật", variable=self.force_var
        ).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(
            options_frame, text="Chế độ im lặng", variable=self.silent_var
        ).grid(row=0, column=1, sticky=tk.W, padx=5)

        # Buttons section
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(
            button_frame,
            text="Bắt đầu cập nhật",
            command=self.start_update,
            width=20,
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.auto_detect_button = ttk.Button(
            button_frame,
            text="Tự động phát hiện",
            command=self.auto_detect_release,
            width=20,
        )
        self.auto_detect_button.grid(row=0, column=1, padx=5)

        self.exit_button = ttk.Button(
            button_frame, text="Thoát", command=self.exit_app, width=20
        )
        self.exit_button.grid(row=0, column=2, padx=5)

        # Log display section
        log_frame = ttk.LabelFrame(main_frame, text="Nhật ký cập nhật", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(4, weight=1)

        # ScrolledText for logs
        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, width=80, height=20, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Configure column weights
        input_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

    def browse_install_dir(self):
        """Browse for installation directory"""
        directory = filedialog.askdirectory(title="Chọn thư mục cài đặt")
        if directory:
            self.install_dir_entry.delete(0, tk.END)
            self.install_dir_entry.insert(0, directory)

    def browse_backup_dir(self):
        """Browse for backup directory"""
        directory = filedialog.askdirectory(title="Chọn thư mục sao lưu")
        if directory:
            self.backup_dir_entry.delete(0, tk.END)
            self.backup_dir_entry.insert(0, directory)

    def setup_logger_redirect(self):
        """Redirect SafeLogger output to GUI safely"""
        # Store original log function for restoration
        if not hasattr(SafeLogger, '_original_log'):
            SafeLogger._original_log = SafeLogger.log
        
        original_log = SafeLogger._original_log
        gui_instance = self

        def gui_log(level: str, message: str):
            # Call original log function (still writes to file)
            original_log(level, message)
            # Also display in GUI if available
            try:
                if gui_instance and gui_instance.log_text:
                    gui_instance.append_log(f"[{level}] {message}")
            except:
                pass  # Fail silently if GUI is not available

        SafeLogger.log = gui_log

    def append_log(self, message: str):
        """Append message to log display"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.root.update_idletasks()

    def auto_detect_release(self):
        """Auto-detect latest release"""
        self.append_log("🔍 Đang tự động phát hiện phiên bản mới nhất...")

        def detect():
            try:
                release_info = get_latest_release_info()
                if release_info:
                    url = release_info["download_url"]
                    version = release_info["version"]

                    # Update GUI in main thread
                    self.root.after(0, lambda: self.url_entry.delete(0, tk.END))
                    self.root.after(0, lambda: self.url_entry.insert(0, url))
                    self.root.after(
                        0,
                        lambda: self.append_log(
                            f"✅ Phát hiện thành công: {version}"
                        ),
                    )
                    self.root.after(0, lambda: self.append_log(f"📥 URL: {url}"))
                    if "published_at" in release_info:
                        self.root.after(
                            0,
                            lambda: self.append_log(
                                f"📅 Ngày phát hành: {release_info['published_at']}"
                            ),
                        )
                else:
                    self.root.after(
                        0,
                        lambda: self.append_log(
                            "❌ Không thể tự động phát hiện phiên bản mới"
                        ),
                    )
                    self.root.after(
                        0,
                        lambda: messagebox.showerror(
                            "Lỗi", "Không thể tự động phát hiện phiên bản mới"
                        ),
                    )
            except Exception as e:
                self.root.after(0, lambda: self.append_log(f"❌ Lỗi: {str(e)}"))
                self.root.after(
                    0, lambda: messagebox.showerror("Lỗi", f"Lỗi: {str(e)}")
                )

        # Run in background thread (daemon=True is OK for auto-detect as it's just a query)
        thread = threading.Thread(target=detect, daemon=True)
        thread.start()

    def start_update(self):
        """Start the update process"""
        if self.is_updating:
            messagebox.showwarning(
                "Cảnh báo", "Quá trình cập nhật đang chạy!"
            )
            return

        # Get values from GUI
        update_url = self.url_entry.get().strip()
        install_dir = self.install_dir_entry.get().strip() or "."
        current_version = self.version_entry.get().strip()
        backup_dir = self.backup_dir_entry.get().strip() or None
        force = self.force_var.get()
        silent = self.silent_var.get()
        process_names_str = self.process_entry.get().strip()
        process_names = (
            [p.strip() for p in process_names_str.split(",") if p.strip()]
            if process_names_str
            else ["main.exe"]
        )

        # Auto-detect if no URL provided
        if not update_url:
            self.append_log("📡 Không có URL, đang tự động phát hiện...")
            release_info = get_latest_release_info()
            if release_info:
                update_url = release_info["download_url"]
                if not current_version:
                    current_version = "1.0.0"
                self.append_log(f"🎯 URL tự động: {update_url}")
                self.append_log(f"📝 Phiên bản: {release_info['version']}")
            else:
                messagebox.showerror(
                    "Lỗi",
                    "Không thể tự động phát hiện phiên bản mới.\nVui lòng nhập URL thủ công.",
                )
                return

        # Confirm update
        if not messagebox.askyesno(
            "Xác nhận",
            f"Bạn có chắc chắn muốn cập nhật?\n\nURL: {update_url}\nThư mục: {install_dir}",
        ):
            return

        # Disable buttons during update
        self.set_buttons_state(tk.DISABLED)
        self.is_updating = True
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

        # Run update in background thread
        def update_task():
            try:
                success = self.update_manager.perform_complete_update(
                    update_url=update_url,
                    install_dir=install_dir,
                    current_version=current_version,
                    backup_dir=backup_dir,
                    force=force,
                    silent=silent,
                    process_names=process_names,
                )

                # Show result in main thread
                if success:
                    self.root.after(
                        0,
                        lambda: messagebox.showinfo(
                            "Thành công", "🎉 Cập nhật hoàn tất thành công!"
                        ),
                    )
                else:
                    self.root.after(
                        0,
                        lambda: messagebox.showerror(
                            "Lỗi", "❌ Cập nhật thất bại! Vui lòng kiểm tra nhật ký."
                        ),
                    )
            except Exception as e:
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Lỗi", f"❌ Lỗi trong quá trình cập nhật:\n{str(e)}"
                    ),
                )
                self.root.after(0, lambda: self.append_log(f"❌ Exception: {str(e)}"))
            finally:
                # Re-enable buttons
                self.root.after(0, lambda: self.set_buttons_state(tk.NORMAL))
                self.is_updating = False

        # Run update in background thread (not daemon - critical operation must complete)
        self.update_thread = threading.Thread(target=update_task)
        self.update_thread.start()

    def set_buttons_state(self, state):
        """Enable or disable all buttons"""
        self.start_button.configure(state=state)
        self.auto_detect_button.configure(state=state)
        self.exit_button.configure(state=state)

    def exit_app(self):
        """Exit the application"""
        if self.is_updating:
            if not messagebox.askyesno(
                "Xác nhận",
                "Quá trình cập nhật đang chạy!\nBạn có chắc chắn muốn thoát?",
            ):
                return
        
        # Wait for update thread to complete if it's running
        if self.update_thread and self.update_thread.is_alive():
            self.append_log("⏳ Đang chờ quá trình cập nhật hoàn tất...")
            self.update_thread.join(timeout=2.0)  # Wait up to 2 seconds
        
        self.root.quit()
        self.root.destroy()


def main():
    """Main entry point for GUI application"""
    root = tk.Tk()
    app = UpdateManagerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
