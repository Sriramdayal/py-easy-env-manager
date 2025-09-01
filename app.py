# gui_app.py
# A graphical user interface for the Python dependency management tool.

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import subprocess
import sys
import os
import threading
import queue
import json
from pathlib import Path

# --- Configuration (defaults) ---
PROJECTS_DIR = Path("./.pyeasyenv_projects")
PYTHON_EXEC = sys.executable # The python interpreter running this script

# Packages that should never be uninstalled
NEVER_UNINSTALL = {"pip", "pip-tools", "pipreqs", "setuptools", "wheel"}

class App(tk.Tk):
    """The main application class for the GUI."""
    def __init__(self):
        super().__init__()
        self.title("Py-Easy-Env: Intelligent Dependency Manager")
        self.geometry("700x680")

        # --- Dynamic State ---
        self.projects = tk.StringVar()
        self.current_project = tk.StringVar()
        self.log_queue = queue.Queue()
        
        self.setup_projects()
        self.create_widgets()
        
        self.after(100, self.process_log_queue)
        if self.project_list:
            self.current_project.set(self.project_list[0])

    def setup_projects(self):
        """Creates the projects directory and loads existing projects."""
        PROJECTS_DIR.mkdir(exist_ok=True)
        self.project_list = [d.name for d in PROJECTS_DIR.iterdir() if d.is_dir()]
        self.log(f"Found {len(self.project_list)} projects.")

    def create_widgets(self):
        """Create and lay out all the GUI widgets."""
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Project Management Frame ---
        project_frame = ttk.LabelFrame(self.main_frame, text="1. Select or Create Project", padding="10")
        project_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        project_frame.columnconfigure(0, weight=1)

        self.project_combo = ttk.Combobox(project_frame, textvariable=self.current_project, values=self.project_list, state="readonly")
        self.project_combo.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        new_project_button = ttk.Button(project_frame, text="New Project...", command=self.create_new_project)
        new_project_button.grid(row=0, column=1, padx=5, pady=5)
        
        sync_button = ttk.Button(project_frame, text="Switch & Sync Environment", command=self.start_sync_task)
        sync_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # --- Dependency Management Frame ---
        deps_frame = ttk.LabelFrame(self.main_frame, text="2. Manage Dependencies", padding="10")
        deps_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        deps_frame.columnconfigure(0, weight=1)
        
        self.dep_entry = ttk.Entry(deps_frame)
        self.dep_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.dep_entry.insert(0, "e.g., flask or requests==2.31.0")

        add_dep_button = ttk.Button(deps_frame, text="Add Dependency", command=self.start_add_dependency_task)
        add_dep_button.grid(row=0, column=1, padx=5, pady=5)
        
        scan_code_button = ttk.Button(deps_frame, text="Scan Code and Add Imports", command=self.start_scan_code_task)
        scan_code_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        # --- Environment Tools Frame ---
        env_tools_frame = ttk.LabelFrame(self.main_frame, text="Environment Tools", padding="10")
        env_tools_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        env_tools_frame.columnconfigure(0, weight=1)
        
        list_button = ttk.Button(env_tools_frame, text="Check: List Installed Packages", command=self.start_list_installed_task)
        list_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # --- Log Frame ---
        log_frame = ttk.LabelFrame(self.main_frame, text="Output Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def log(self, message):
        self.log_queue.put(message)

    def process_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.after(100, self.process_log_queue)

    def set_all_buttons_state(self, state):
        for child in self.main_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Button, ttk.Combobox, ttk.Entry)):
                        widget.config(state=state)

    def create_new_project(self):
        project_name = simpledialog.askstring("New Project", "Enter a name for the new project:")
        if project_name and project_name not in self.project_list:
            (PROJECTS_DIR / project_name).mkdir(exist_ok=True)
            self.project_list.append(project_name)
            self.project_combo['values'] = self.project_list
            self.current_project.set(project_name)
            self.log(f"\n--- Created new project: {project_name} ---")
        elif project_name:
            messagebox.showerror("Error", "A project with that name already exists.")
            
    def get_project_paths(self):
        proj_name = self.current_project.get()
        if not proj_name:
            return None, None
        proj_dir = PROJECTS_DIR / proj_name
        return proj_dir / "requirements.in", proj_dir / "requirements.txt"

    def run_command(self, command, description):
        """Synchronous command runner for internal logic."""
        self.log(f"\n--- {description} ---")
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace'
            )
            stdout, stderr = process.communicate()
            if stdout: self.log(stdout.strip())
            if stderr: self.log(f"Log: {stderr.strip()}")
            
            if process.returncode == 0:
                self.log("--- Success! ---")
                return 0, stdout
            else:
                self.log(f"--- Command failed with exit code {process.returncode} ---")
                # Handle missing tool dependencies
                tool_name = None
                if stderr and ("ModuleNotFoundError" in stderr or "Error while finding module specification" in stderr):
                    if "pipreqs" in " ".join(command): tool_name = 'pipreqs'
                    elif "piptools" in " ".join(command): tool_name = 'pip-tools'
                
                if tool_name:
                    install_ok = self.prompt_to_install_tool(tool_name)
                    if install_ok:
                        self.log("--- Retrying original command... ---")
                        return self.run_command(command, description) # Retry the command

                return process.returncode, stderr
        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")
            return 1, str(e)
            
    def prompt_to_install_tool(self, tool_name):
        """Prompts user to install a tool and runs the installation. Returns True on success."""
        install_ok = messagebox.askyesno(
            "Missing Dependency",
            f"A required module for '{tool_name}' is missing. Would you like to reinstall it now?"
        )
        if install_ok:
            install_command = [PYTHON_EXEC, "-m", "pip", "install", "--force-reinstall", tool_name]
            return_code, _ = self.run_command(install_command, f"Reinstalling {tool_name}")
            return return_code == 0
        return False

    def start_task(self, target_function, *args):
        self.set_all_buttons_state(tk.DISABLED)
        thread = threading.Thread(target=target_function, args=args, daemon=True)
        thread.start()
        self.check_thread(thread)

    def check_thread(self, thread):
        if thread.is_alive():
            self.after(100, lambda: self.check_thread(thread))
        else:
            self.set_all_buttons_state(tk.NORMAL)
            # Make combobox readonly again
            self.project_combo.config(state="readonly")
            
    def add_dependency_and_sync(self, dependency=None, dependencies_from_scan=None):
        """The core logic for adding dependencies and updating the environment."""
        req_in_path, req_txt_path = self.get_project_paths()
        if not req_in_path:
            self.log("Error: No project selected.")
            return

        if dependency:
            with open(req_in_path, "a") as f:
                f.write(f"{dependency}\n")
            self.log(f"Added '{dependency}' to '{req_in_path.name}'.")

        if dependencies_from_scan:
             with open(req_in_path, "w") as f:
                for dep in dependencies_from_scan:
                    f.write(f"{dep}\n")
             self.log(f"Saved {len(dependencies_from_scan)} scanned imports to '{req_in_path.name}'.")
        
        # Automatic Lock and Sync
        self.log("Automatically updating lockfile and syncing environment...")
        self.run_command([PYTHON_EXEC, "-m", "piptools", "compile", str(req_in_path), "--output-file", str(req_txt_path)], "Locking dependencies")
        self.run_command([PYTHON_EXEC, "-m", "piptools", "sync", str(req_txt_path)], "Syncing environment")

    def start_add_dependency_task(self):
        dep = self.dep_entry.get()
        if not dep or "e.g.," in dep:
            self.log("Error: Please enter a valid package name.")
            return
        self.start_task(self.add_dependency_and_sync, dep)

    def start_scan_code_task(self):
        self.start_task(self.scan_and_add_dependencies)

    def scan_and_add_dependencies(self):
        """Scans code and then adds found dependencies."""
        self.log("Scanning code for imports...")
        # Use pipreqs to get a list of dependencies
        return_code, stdout = self.run_command([PYTHON_EXEC, "-m", "pipreqs.pipreqs", "."], "Scanning for imports")
        if return_code == 0 and stdout:
            dependencies = [line for line in stdout.strip().split('\n') if line]
            if dependencies:
                self.add_dependency_and_sync(dependencies_from_scan=dependencies)
            else:
                self.log("No external imports found in the code.")
        else:
            self.log("Could not determine dependencies from code scan.")

    def start_sync_task(self):
        req_in_path, req_txt_path = self.get_project_paths()
        if not req_in_path:
            self.log("Error: No project selected.")
            return
        self.start_task(self.run_command, [PYTHON_EXEC, "-m", "piptools", "sync", str(req_txt_path)], "Syncing environment")

    def start_list_installed_task(self):
        """Starts the task to list installed packages."""
        self.start_task(self.list_installed_packages)

    def list_installed_packages(self):
        """The core logic for listing installed packages."""
        command = [PYTHON_EXEC, "-m", "pip", "list"]
        self.run_command(command, "Listing currently installed packages")


if __name__ == "__main__":
    app = App()
    app.mainloop()

