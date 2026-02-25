import tkinter as tk
from tkinter import simpledialog, scrolledtext
import sys
import os
import threading
import logging
import queue

# Ensure we can find 'sipp' if it's in the local bin directory
local_bin = os.path.join(os.getcwd(), 'bin')
if os.path.isdir(local_bin):
    os.environ["PATH"] += os.pathsep + local_bin

try:
    import pysipp
except ImportError:
    # If not installed, try to import from local source
    sys.path.insert(0, os.getcwd())
    import pysipp

class TextHandler(logging.Handler):
    """This class allows you to log to a Tkinter Text or ScrolledText widget"""
    def __init__(self, text):
        logging.Handler.__init__(self)
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            self.text.yview(tk.END)
        # Check if the widget still exists
        try:
            self.text.after(0, append)
        except Exception:
            pass

class SippGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pysipp Voice/Text Control")
        self.root.geometry("600x500")

        # Command Input
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=10, fill=tk.X, padx=10)

        self.cmd_label = tk.Label(self.input_frame, text="Command:")
        self.cmd_label.pack(side=tk.LEFT)

        self.cmd_entry = tk.Entry(self.input_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind('<Return>', lambda event: self.run_command())

        # Buttons
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=5)

        self.voice_btn = tk.Button(self.btn_frame, text="Simulate Voice", command=self.simulate_voice)
        self.voice_btn.pack(side=tk.LEFT, padx=5)

        self.run_btn = tk.Button(self.btn_frame, text="Run Command", command=self.run_command, bg="green", fg="white")
        self.run_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = tk.Button(self.btn_frame, text="Clear Log", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Output Log
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=20)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Setup Logging
        self.setup_logging()

        self.log("Welcome to Pysipp Control. Type 'help' for commands.")

    def setup_logging(self):
        self.logger = logging.getLogger("pysipp")
        self.logger.setLevel(logging.DEBUG)

        handler = TextHandler(self.log_area)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Also log to our own internal logger for gui messages
        self.gui_logger = logging.getLogger("gui")
        self.gui_logger.setLevel(logging.INFO)
        self.gui_logger.addHandler(handler)

    def log(self, message):
        self.gui_logger.info(message)

    def clear_log(self):
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')

    def simulate_voice(self):
        text = simpledialog.askstring("Voice Input", "Speak (type) your command:")
        if text:
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, text)
            self.run_command()

    def run_command(self):
        cmd_text = self.cmd_entry.get().strip()
        if not cmd_text:
            return

        self.log(f"Executing: {cmd_text}")
        self.cmd_entry.delete(0, tk.END)

        # Run in a separate thread to not block GUI
        threading.Thread(target=self.execute_pysipp, args=(cmd_text,), daemon=True).start()

    def execute_pysipp(self, cmd_text):
        parts = cmd_text.split()
        if not parts:
            return

        command = parts[0].lower()
        args = parts[1:]

        try:
            if command == "client":
                self.run_client(args)
            elif command == "server":
                self.run_server(args)
            elif command == "scenario":
                self.run_scenario(args)
            elif command == "help":
                self.show_help()
            else:
                self.log(f"Unknown command: {command}")
        except Exception as e:
            self.log(f"Error executing command: {e}")

    def run_client(self, args):
        # Expected format: client <dest_ip> <dest_port>
        if len(args) < 2:
            self.log("Usage: client <dest_ip> <dest_port>")
            return

        dest_ip = args[0]
        try:
            dest_port = int(args[1])
        except ValueError:
             self.log("Port must be an integer")
             return

        self.log(f"Launching Client to {dest_ip}:{dest_port}")

        try:
            c = pysipp.client(destaddr=(dest_ip, dest_port))
            self.log(f"Command: {c.cmd}")
            c() # Run synchronously in this thread
            self.log("Client execution finished.")
        except Exception as e:
            self.log(f"Client failed: {e}")

    def run_server(self, args):
        # Expected format: server <local_ip> <local_port>
        if len(args) < 2:
             self.log("Usage: server <local_ip> <local_port>")
             return

        local_ip = args[0]
        try:
            local_port = int(args[1])
        except ValueError:
             self.log("Port must be an integer")
             return

        self.log(f"Launching Server on {local_ip}:{local_port}")
        try:
            s = pysipp.server(srcaddr=(local_ip, local_port))
            self.log(f"Command: {s.cmd}")
            s()
            self.log("Server execution finished.")
        except Exception as e:
            self.log(f"Server failed: {e}")

    def run_scenario(self, args):
        if not args:
            self.log("Usage: scenario <path>")
            return

        path = args[0]
        self.log(f"Running scenario from {path}")
        try:
            scen = pysipp.scenario(dirpath=path)
            scen()
            self.log("Scenario execution finished.")
        except Exception as e:
             self.log(f"Scenario failed: {e}")

    def show_help(self):
        help_text = """Available Commands:
- client <dest_ip> <dest_port>: Run a SIPp client.
- server <local_ip> <local_port>: Run a SIPp server.
- scenario <path>: Run a SIPp scenario from a directory.
- help: Show this help message.
"""
        self.log(help_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = SippGUI(root)
    root.mainloop()
