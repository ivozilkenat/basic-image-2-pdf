from core.img2pdf import IMG2PDF
from core.validFileName import is_valid_filename

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import threading
import os
import sys


class CallbackOutRedirect:
    def __init__(self, callback):
        self.callback = callback
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        if "\n" in string:
            self.flush()

    def flush(self):
        self.callback(self.buffer)
        self.buffer = ""


class IMG2PDFApplication:
    def __init__(self):
        self.window = None
        self.entry_function = IMG2PDF.run_img2pdf
        self.script_running = False

        self._build()
        self._setup_redirect()

    def _setup_redirect(self):
        sys.stdout = CallbackOutRedirect(lambda *args, **kwargs: self.print_console(*args, **kwargs, end=""))
        sys.stderr = CallbackOutRedirect(lambda *args, **kwargs: self.print_console(*args, **kwargs, end="", alert=True))

    def run_script(self, dir_path_entry, dir_target_path_entry, output_name_entry, update_progress_callback):
        def __inner(*args, **kwargs):
            if self.script_running:
                print("Programm wird bereits ausgeführt!")
                return

            self.script_running = True

            dir_path = dir_path_entry.get()
            output_dir = dir_target_path_entry.get()
            output_name = output_name_entry.get()
            output_path = os.path.join(output_dir, output_name + ".pdf")
            if not self.valid_args(dir_path, output_dir, output_name):
                return
            # Assuming main.py has a function named 'process_file' that takes dir_path and output_name
            self.entry_function(dir_path, output_path, update_progress_callback)

            self.script_running = False
        return __inner

    def valid_args(self, dir_path, output_dir, output_name):
        valid_path = os.path.isdir(dir_path)
        if not valid_path:
            print(f"Der gewählte  Quellpfad ist ungültig: '{dir_path}'")
            return False
        valid_path_out = os.path.isdir(output_dir)
        if not valid_path_out:
            print(f"Der gewählte Zielpfad ist ungültig: '{output_dir}'")
            return False
        valid_output_name = is_valid_filename(output_name)
        if not valid_output_name:
            print(f"Der gewählte Dateiname ist ungültig: '{output_name}'")
            return False
        return True

    def update_progress(self, progress_var):
        def __inner(progress):
            progress_var.set(progress)
            self.window.update_idletasks()
        return __inner

    def select_folder(self, dir_path_entry):
        def __inner():
            dir_path = filedialog.askdirectory(initialdir=os.getcwd())
            dir_path_entry.delete(0, tk.END)
            dir_path_entry.insert(0, dir_path)
        return __inner

    def print_console(self, message, prefix="> ", end="\n", alert=False):
        message = prefix + message + end
        if alert:
            self._update_console(message, config_tag="red_text")
        else:
            self._update_console(message)

    def _update_console(self, message, config_tag=None):
        self.console.config(state=tk.NORMAL)  # Temporarily enable the widget to modify it
        if config_tag is not None:
            self.console.insert(tk.END, message, config_tag)
        else:
            self.console.insert(tk.END, message)
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)  # Disable the widget again


    def _build(self):
        self.window = tk.Tk()
        self.window.title("Bildserie zu PDF")

        # Window geometry
        self.window.geometry("800x250")
        self.window.grid_columnconfigure(1, weight=10)
        self.window.grid_columnconfigure(2, weight=3)
        self.window.grid_rowconfigure(index=6, weight=1)

        # Source Dir Path selection
        ttk.Label(self.window, text="Quellverzeichnispfad:").grid(row=0, column=0, sticky='ew', padx=10, pady=(5, 5))
        dir_path_entry = ttk.Entry(self.window, width=40)
        dir_path_entry.grid(row=0, column=1, sticky="ew", pady=(5, 5))
        ttk.Button(self.window, text="Suche", command=self.select_folder(dir_path_entry)).grid(row=0, column=2, sticky="ew", padx=5, pady=(5, 5))

        # Target Dir Path selection
        ttk.Label(self.window, text="Zielverzeichnispfad:").grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 5))
        dir_target_path_entry = ttk.Entry(self.window, width=40)
        dir_target_path_entry.grid(row=1, column=1, sticky="ew", pady=(0, 5))
        ttk.Button(self.window, text="Suche", command=self.select_folder(dir_target_path_entry)).grid(row=1, column=2, sticky="ew", padx=5, pady=(0, 5))

        # Output File Name entry
        ttk.Label(self.window, text="Ausgabe-Dateiname:").grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 10))
        output_name_entry = ttk.Entry(self.window, width=40)
        output_name_entry.grid(row=2, column=1, sticky="ew", pady=(0, 10))

        # Horizontal separator
        separator_horizontal = ttk.Separator(self.window, orient='horizontal')
        separator_horizontal.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5)

        # Run button
        ttk.Button(
            self.window,
            text="Starten",
            command=lambda: threading.Thread(
                target=self.run_script(dir_path_entry, dir_target_path_entry, output_name_entry, self.update_progress(progress_var))
            ).start()
        ).grid(row=4, column=0, columnspan=3, sticky="ew", padx=5)

        # Progress Bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(self.window, maximum=100, variable=progress_var, length=200)
        progress_bar.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5)

        # Console area
        self.console = tk.Text(self.window, width=50, state=tk.DISABLED)
        self.console.grid(row=6, column=0, columnspan=3, sticky="ew", padx=5)
        self.console.tag_configure("red_text", foreground="red")

    def print_intro(self):
        print("[ Willkommen beim Bild zu PDF Konvertierer 3000 ]")
        print("1.) Wählen zwei Ordner als Quell-/Zielverzeichnis")
        print("2.) Wähle den Namen der Ausgabedatei (ohne .pdf)")
        print("3.) Klicke auf 'Start'")
        print("4.) Abwarten und Tee trinken")

    def run(self):
        self.print_intro()
        self.window.mainloop() # Blocking


if __name__ == "__main__":
    app = IMG2PDFApplication()
    app.run()

    #input_dir = 'example_source'  # Change this to your directory path
    #output_pdf = 'output.pdf'



