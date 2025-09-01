# gui_app.py
# A graphical user interface for the Python dependency management tool.

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import sys
import os
import threading
import queue

# --- Configuration (defaults) ---
LOCKED_FILE = "requirements.txt"
PYTHON_EXEC = sys.executable # The python interpreter running this script

class App(tk.Tk):
    """The main application class for the GUI."""
    def __init__(self):
        super().__init__()
        self.title("Py-Easy-Env: Dependency Manager")
        self.geometry("700x550")

        # --- Dynamic State ---
        self.input_file = tk.StringVar(value="requirements.in")
        self.log_queue = queue.Queue()
        self.create_widgets()
        self.check_requirements_file()
        self.after(100, self.process_log_queue)

    def create_widgets(self):
        """Create and lay out all the GUI widgets."""
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # --- File Selection Frame ---
        file_frame = ttk.LabelFrame(self.main_frame, text="Input File for Locking", padding="10")
        file_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        file_label = ttk.Label(file_frame, textvariable=self.input_file, foreground="blue")
        file_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        select_button = ttk.Button(file_frame, text="Select File...", command=self.select_input_file)
        select_button.grid(row=0, column=1, padx=5, pady=5)

        # --- Controls Frame ---
        controls_frame = ttk.LabelFrame(self.main_frame, text="Workflow", padding="10")
        controls_frame.pack(fill=tk.X, expand=False)
        controls_frame.columnconfigure((0, 1), weight=1)

        self.scan_code_button = ttk.Button(
            controls_frame, text="1. Scan Code for Imports", command=self.start_scan_code_task
        )
        self.scan_code_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.lock_button = ttk.Button(
            controls_frame, text="2. Create Lockfile", command=self.start_lock_task
        )
        self.lock_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.sync_button = ttk.Button(
            controls_frame, text="3. Sync (Install/Uninstall)", command=self.start_sync_task
        )
        self.sync_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.scan_button = ttk.Button(
            controls_frame, text="Check: List Installed Packages", command=self.start_scan_task
        )
        self.scan_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # --- Log Frame ---
        log_frame = ttk.LabelFrame(self.main_frame, text="Output Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def select_input_file(self):
        """Opens a file dialog to select the input requirements file."""
        filepath = filedialog.askopenfilename(
            title="Select a requirements file",
            filetypes=(("Requirements files", "*.in *.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.input_file.set(filepath)
            self.log(f"\nInfo: Input file set to '{filepath}'")

    def log(self, message):
        """Add a message to the log text widget in a thread-safe way."""
        self.log_queue.put(message)

    def process_log_queue(self):
        """Process messages from the log queue and update the GUI."""
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.after(100, self.process_log_queue)

    def set_buttons_state(self, state):
        """Enable or disable the action buttons."""
        self.scan_code_button.config(state=state)
        self.scan_button.config(state=state)
        self.lock_button.config(state=state)
        self.sync_button.config(state=state)

    def check_requirements_file(self):
        """Checks if the default requirements.in exists and logs a message."""
        input_path = self.input_file.get()
        if not os.path.exists(input_path):
            self.log(f"Info: Default file '{input_path}' not found.")
            if input_path == "requirements.in":
                self.log("Tip: Use 'Scan Code for Imports' to generate it automatically.")
        else:
            self.log(f"Info: Found '{input_path}'. Ready to create a lockfile.")

    def run_command_in_thread(self, command, description):
        """Runs a subprocess command, logging its output in real-time."""
        self.log(f"\n--- {description} ---")
        try:
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', errors='replace'
            )
            
            is_pip_compile = "piptools" in command and "compile" in command
            
            for line in iter(process.stdout.readline, ''): self.log(line.strip())
            for line in iter(process.stderr.readline, ''):
                if is_pip_compile: self.log(line.strip())
                else: self.log(f"Log: {line.strip()}")
            
            process.wait()
            if process.returncode == 0: self.log("--- Success! ---")
            else:
                self.log(f"--- Command failed with exit code {process.returncode} ---")
                
                # Check for module not found error and prompt for installation
                tool_name = None
                if "No module named pipreqs" in str(process.stderr.read()): tool_name = 'pipreqs'
                elif "No module named piptools" in str(process.stderr.read()): tool_name = 'pip-tools'
                
                if tool_name:
                    install_ok = messagebox.askyesno(
                        "Missing Dependency",
                        f"The tool '{tool_name}' is not installed in this environment. Would you like to install it now?"
                    )
                    if install_ok:
                        install_command = [PYTHON_EXEC, "-m", "pip", "install", tool_name]
                        self.start_task(self.run_command_in_thread, install_command, f"Installing {tool_name}")
                    else:
                        self.log(f"Please install '{tool_name}' manually to proceed.")

        except Exception as e:
            self.log(f"An unexpected error occurred: {e}")

    def start_task(self, target_function, *args):
        """Starts a new thread for a given task to avoid freezing the GUI."""
        self.set_buttons_state(tk.DISABLED)
        thread = threading.Thread(target=target_function, args=args, daemon=True)
        thread.start()
        self.check_thread(thread)

    def check_thread(self, thread):
        """If the thread is finished, re-enable the buttons."""
        if thread.is_alive():
            self.after(100, lambda: self.check_thread(thread))
        else:
            self.set_buttons_state(tk.NORMAL)

    def start_scan_code_task(self):
        """Scans code for imports and saves them to 'requirements.in'."""
        output_file = "requirements.in"
        scan_command = [PYTHON_EXEC, "-m", "pipreqs.pipreqs", ".", "--force", "--savepath", output_file]
        description = f"Scanning code and saving imports to '{output_file}'"
        self.start_task(self.run_command_in_thread, scan_command, description)
            
    def start_scan_task(self):
        """Lists all packages currently installed in the environment."""
        scan_command = [PYTHON_EXEC, "-m", "pip", "list"]
        description = "Scanning installed packages in the environment"
        self.start_task(self.run_command_in_thread, scan_command, description)

    def start_lock_task(self):
        """Creates a lockfile from the selected input file."""
        current_input_file = self.input_file.get()
        if not os.path.exists(current_input_file):
            self.log(f"Error: Input file '{current_input_file}' not found. Please select or generate it.")
            return
        lock_command = [PYTHON_EXEC, "-m", "piptools", "compile", current_input_file, "--output-file", LOCKED_FILE]
        description = f"Creating lockfile from '{os.path.basename(current_input_file)}'"
        self.start_task(self.run_command_in_thread, lock_command, description)

    def start_sync_task(self):
        """Installs/uninstalls packages to match the lockfile."""
        if not os.path.exists(LOCKED_FILE):
            self.log(f"Error: '{LOCKED_FILE}' not found. Please create the lockfile first.")
            return
        sync_command = [PYTHON_EXEC, "-m", "piptools", "sync", LOCKED_FILE]
        description = f"Syncing environment with '{LOCKED_FILE}'"
        self.start_task(self.run_command_in_thread, sync_command, description)

if __name__ == "__main__":
    app = App()
    app.mainloop()

