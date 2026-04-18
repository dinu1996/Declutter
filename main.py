import ctypes
import sys
import os
import threading
import datetime
from tkinter import messagebox
import customtkinter as ctk

from app_fetcher import AppFetcher
from file_scanner import FileScanner

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

class SystemCleanerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Declutter")
        self.geometry("900x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.all_apps = []
        self.file_scanner = FileScanner(finished_callback=self.on_scan_finished)

        self.setup_ui()
        
        # Load apps in background
        self.after(100, self.load_apps)

    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        self.tab_apps = self.tabview.add("Installed Apps")
        self.tab_files = self.tabview.add("Large Files")

        self.setup_apps_tab()
        self.setup_files_tab()

    # --- Installed Apps Tab ---
    def setup_apps_tab(self):
        self.apps_top_frame = ctk.CTkFrame(self.tab_apps, fg_color="transparent")
        self.apps_top_frame.pack(fill="x", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace("w", self.filter_apps)
        self.search_entry = ctk.CTkEntry(self.apps_top_frame, textvariable=self.search_var, placeholder_text="Search apps...", width=300)
        self.search_entry.pack(side="left")

        self.refresh_apps_btn = ctk.CTkButton(self.apps_top_frame, text="Refresh", command=self.load_apps, width=100)
        self.refresh_apps_btn.pack(side="right")

        self.apps_status_label = ctk.CTkLabel(self.apps_top_frame, text="Loading apps...", text_color="gray")
        self.apps_status_label.pack(side="right", padx=10)

        self.apps_scrollable_frame = ctk.CTkScrollableFrame(self.tab_apps)
        self.apps_scrollable_frame.pack(fill="both", expand=True)

    def load_apps(self):
        self.apps_status_label.configure(text="Loading apps...")
        self.refresh_apps_btn.configure(state="disabled")
        
        # Clear current list
        for widget in self.apps_scrollable_frame.winfo_children():
            widget.destroy()

        threading.Thread(target=self._fetch_apps_thread, daemon=True).start()

    def _fetch_apps_thread(self):
        self.all_apps = AppFetcher.get_all_apps()
        self.after(0, self._render_apps_list, self.all_apps)

    def _render_apps_list(self, apps_to_display):
        for widget in self.apps_scrollable_frame.winfo_children():
            widget.destroy()

        for app in apps_to_display:
            row_frame = ctk.CTkFrame(self.apps_scrollable_frame)
            row_frame.pack(fill="x", pady=2, padx=5)
            
            info_text = f"{app['name']} (v{app['version']}) - [{app['source']}]"
            label = ctk.CTkLabel(row_frame, text=info_text, anchor="w", justify="left")
            label.pack(side="left", padx=10, pady=5, fill="x", expand=True)

            uninstall_btn = ctk.CTkButton(
                row_frame, text="Uninstall", width=80, fg_color="#c0392b", hover_color="#e74c3c"
            )
            uninstall_btn.configure(command=lambda a=app, r=row_frame, b=uninstall_btn: self.uninstall_app(a, r, b))
            uninstall_btn.pack(side="right", padx=10, pady=5)

        self.apps_status_label.configure(text=f"Total: {len(apps_to_display)}")
        self.refresh_apps_btn.configure(state="normal")

    def filter_apps(self, *args):
        query = self.search_var.get().lower()
        if not query:
            filtered = self.all_apps
        else:
            filtered = [app for app in self.all_apps if query in app['name'].lower() or query in app['source'].lower()]
        self._render_apps_list(filtered)

    def uninstall_app(self, app_info, row_frame, uninstall_btn):
        confirm = messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall {app_info['name']}?\n\nSource: {app_info['source']}")
        if confirm:
            uninstall_btn.configure(state="disabled", text="Uninstalling...")
            threading.Thread(target=self._uninstall_thread, args=(app_info, row_frame, uninstall_btn), daemon=True).start()

    def _uninstall_thread(self, app_info, row_frame, uninstall_btn):
        success, msg = AppFetcher.uninstall_app(app_info)
        self.after(0, self._uninstall_finished, success, msg, row_frame, uninstall_btn, app_info)

    def _uninstall_finished(self, success, msg, row_frame, uninstall_btn, app_info):
        if success:
            messagebox.showinfo("Uninstall Successful", f"Successfully uninstalled {app_info['name']}.")
            row_frame.destroy()
        else:
            if uninstall_btn.winfo_exists():
                uninstall_btn.configure(state="normal", text="Uninstall")
            messagebox.showerror("Uninstall Failed", f"Failed to uninstall {app_info['name']}:\n\n{msg}")

    # --- Large Files Tab ---
    def setup_files_tab(self):
        self.files_top_frame = ctk.CTkFrame(self.tab_files, fg_color="transparent")
        self.files_top_frame.pack(fill="x", pady=(0, 10))

        self.scan_btn = ctk.CTkButton(self.files_top_frame, text="Scan C: Drive", command=self.start_scan, width=150)
        self.scan_btn.pack(side="left")

        self.files_status_label = ctk.CTkLabel(self.files_top_frame, text="Ready", text_color="gray")
        self.files_status_label.pack(side="left", padx=10)

        self.files_scrollable_frame = ctk.CTkScrollableFrame(self.tab_files)
        self.files_scrollable_frame.pack(fill="both", expand=True)

    def start_scan(self):
        self.scan_btn.configure(state="disabled")
        self.files_status_label.configure(text="Scanning C:\\ ... This may take a few minutes.")
        
        for widget in self.files_scrollable_frame.winfo_children():
            widget.destroy()

        self.file_scanner.start_scan("C:\\")

    def on_scan_finished(self, files):
        self.after(0, self._render_files_list, files)

    def _render_files_list(self, files):
        self.files_status_label.configure(text=f"Scan complete. Found top {len(files)} files.")
        self.scan_btn.configure(state="normal")

        for size, path, timestamp in files:
            row_frame = ctk.CTkFrame(self.files_scrollable_frame)
            row_frame.pack(fill="x", pady=2, padx=5)

            name = os.path.basename(path)
            size_str = format_size(size)
            try:
                mod_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
            except:
                mod_time = "Unknown"

            info_text = f"{name} | {size_str} | Mod: {mod_time}\n{path}"
            label = ctk.CTkLabel(row_frame, text=info_text, anchor="w", justify="left")
            label.pack(side="left", padx=10, pady=5, fill="x", expand=True)

            del_btn = ctk.CTkButton(
                row_frame, text="Delete", width=80, fg_color="#c0392b", hover_color="#e74c3c",
                command=lambda p=path, r=row_frame: self.delete_file(p, r)
            )
            del_btn.pack(side="right", padx=10, pady=5)

    def delete_file(self, path, row_frame):
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete this file?\n\n{path}")
        if confirm:
            success, msg = FileScanner.delete_file(path, use_recycle_bin=False)
            if success:
                row_frame.destroy()
            else:
                messagebox.showerror("Error", f"Failed to delete file:\n{msg}")

if __name__ == "__main__":
    if not is_admin():
        # Re-run the program with admin rights
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to acquire admin privileges: {e}")
        sys.exit()
    
    app = SystemCleanerApp()
    app.mainloop()
