import subprocess
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import urllib.request
import zipfile
import shutil
import webbrowser

# --- CONFIGURATION (MODIFIABLE) ---
# The name of the Wine prefix we will create
WINE_PREFIX_NAME = "RobloxPrefix"

# Dictionary of versions and their download URLs
ROBLOX_VERSIONS = {
    "Mid 2007": "https://github.com/MaximumADHD/Roblox-2007-Client/archive/refs/heads/main.zip",
    "Mid 2008": "https://github.com/MaximumADHD/Roblox-2008-Client/archive/refs/heads/master.zip",
    "Late 2009": "https://github.com/MaximumADHD/Roblox-2009-Client/archive/refs/heads/master.zip"
}

# Dictionary for specific executable paths
EXECUTABLE_PATHS = {
    "Mid 2007": "Roblox.exe",
    "Mid 2008": "Roblox.exe",
    "Late 2009": "RobloxApp.exe"
}

# --- DO NOT MODIFY THE LINES BELOW ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Archivum Launcher")
        self.geometry("450x450")
        self.create_widgets()
        # Set the default version
        self.version_var.set("Mid 2007")

    def create_widgets(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("Helvetica", 12), padding=10)
        self.style.configure("TLabel", font=("Helvetica", 10))

        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        title_label = ttk.Label(main_frame, text="Archivum Launcher", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)

        # Version selection
        version_frame = ttk.Frame(main_frame)
        version_frame.pack(pady=10)

        version_label = ttk.Label(version_frame, text="Select Version:", font=("Helvetica", 10, "bold"))
        version_label.pack(side="left", padx=(0, 10))

        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(version_frame, textvariable=self.version_var, state="readonly")
        self.version_combo['values'] = list(ROBLOX_VERSIONS.keys())
        self.version_combo.pack(side="left")

        # Buttons
        install_button = ttk.Button(main_frame, text="1. Install/Update Wine & App", command=self.run_installation_thread)
        install_button.pack(pady=10, fill="x")
        
        play_button = ttk.Button(main_frame, text="2. Play Game", command=self.run_play_thread)
        play_button.pack(pady=10, fill="x")

        open_folder_button = ttk.Button(main_frame, text="3. Open Client Folder", command=self.open_folder)
        open_folder_button.pack(pady=10, fill="x")
        
        # The 'Fix Camera & Mouse' button has been removed from this section.
        
        credits_button = ttk.Button(main_frame, text="4. Credits", command=self.show_credits)
        credits_button.pack(pady=10, fill="x")
        
        self.status_label = ttk.Label(main_frame, text="Status: Ready", foreground="blue")
        self.status_label.pack(pady=10)

    def set_status(self, text, color="blue"):
        self.status_label.config(text=f"Status: {text}", foreground=color)
        self.update_idletasks()

    def run_command(self, command, message):
        self.set_status(f"Running: {message}")
        try:
            process = subprocess.Popen(command, shell=True, executable="/bin/bash",
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                self.set_status(f"Error: {message} failed. Check console for details.", "red")
                print(f"--- Command Failed: {message} ---")
                print(f"Error Code: {process.returncode}")
                print(f"Output:\n{stdout}\n{stderr}")
                return False
            self.set_status(f"Completed: {message}", "green")
            return True
        except Exception as e:
            self.set_status(f"Fatal Error: {e}", "red")
            print(f"--- Fatal Error: {e} ---")
            print(e)
            return False

    def download_and_extract(self, version_name):
        self.set_status(f"Downloading and extracting {version_name}...")
        app_folder = os.path.join(os.path.expanduser("~"), "Archivum-Clients", version_name.replace(" ", ""))
        zip_file_path = os.path.join(os.path.expanduser("~"), "Archivum-Clients", f"{version_name.replace(' ', '')}.zip")

        if os.path.exists(app_folder):
            self.set_status(f"{version_name} already exists. Skipping download.", "green")
            return app_folder

        os.makedirs(os.path.dirname(zip_file_path), exist_ok=True)
        
        try:
            # Download the file
            self.set_status(f"Downloading {version_name}...", "blue")
            urllib.request.urlretrieve(ROBLOX_VERSIONS[version_name], zip_file_path)

            # Extract the file
            self.set_status(f"Extracting {version_name}...", "blue")
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                first_dir = zip_ref.namelist()[0]
                target_dir = os.path.join(os.path.expanduser("~"), "Archivum-Clients")
                zip_ref.extractall(target_dir)
                
                extracted_folder = os.path.join(target_dir, first_dir.split("/")[0])
                if os.path.exists(app_folder):
                    shutil.rmtree(app_folder)
                shutil.move(extracted_folder, app_folder)

            os.remove(zip_file_path)
            self.set_status(f"Successfully installed {version_name}.", "green")
            return app_folder
        except Exception as e:
            self.set_status(f"Error during download/extraction: {e}", "red")
            return None

    def install_sequence(self):
        self.set_status("Starting full installation...")
        
        # Step 1: Remove old Wine & Winetricks
        if not self.run_command("sudo apt purge wine -y", "Removing old Wine"): return
        if not self.run_command("sudo apt remove winetricks -y", "Removing old Winetricks"): return
        
        # Step 2: Add WineHQ repo and install
        if not self.run_command(
            "sudo dpkg --add-architecture i386 && "
            "sudo mkdir -pm755 /etc/apt/keyrings && "
            "sudo wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key && "
            "sudo wget -O /etc/apt/sources.list.d/winehq-jammy.sources https://dl.winehq.org/wine-builds/ubuntu/dists/jammy/winehq-jammy.sources",
            "Adding WineHQ repository"
        ): return
        
        if not self.run_command("sudo apt update", "Updating repositories"): return
        if not self.run_command("sudo apt install --install-recommends winehq-stable -y", "Installing WineHQ stable"): return
        
        # Step 3: Install updated Winetricks
        if not self.run_command(
            "cd ~ && wget https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks && "
            "chmod +x winetricks && sudo mv winetricks /usr/local/bin",
            "Installing updated Winetricks"
        ): return

        # Step 4: Create 32-bit Wine prefix
        wine_prefix_path = os.path.expanduser(f"~/{WINE_PREFIX_NAME}")
        if os.path.exists(wine_prefix_path):
            self.set_status("Removing old Wine prefix...", "orange")
            self.run_command(f"rm -r {wine_prefix_path}", "Removing old prefix")
        
        os.environ['WINEARCH'] = 'win32'
        os.environ['WINEPREFIX'] = wine_prefix_path
        if not self.run_command("winecfg", "Initializing new Wine prefix"): return
        
        # Step 5: Install core dependencies
        if not self.run_command(f"winetricks vcrun2005", "Installing vcrun2005"): return
        if not self.run_command(f"winetricks vcrun2008", "Installing vcrun2008"): return
        if not self.run_command(f"winetricks vcrun2010", "Installing vcrun2010"): return
        
        # Step 6: Install IE, DirectX and other components to fix navigation and rendering errors
        if not self.run_command(f"winetricks ie8", "Installing Internet Explorer 8"): return
        if not self.run_command(f"winetricks corefonts", "Installing core fonts"): return
        if not self.run_command(f"winetricks d3dx9", "Installing DirectX 9"): return
        if not self.run_command(f"winetricks d3dcompiler_43", "Installing DirectX Shader Compiler"): return

        self.set_status("Installation complete! You can now Play.", "green")

    def run_play(self):
        selected_version = self.version_var.get()
        if not selected_version:
            messagebox.showerror("Error", "Please select a version.")
            return

        # The specific popup for the 2009 client has been removed.
        # The game will now launch directly for all versions.

        app_folder = self.download_and_extract(selected_version)
        if not app_folder:
            return

        executable_name = EXECUTABLE_PATHS.get(selected_version)
        APP_PATH = os.path.join(app_folder, executable_name)
        
        if not os.path.exists(APP_PATH):
            self.set_status("Error: Executable not found. Please check the folder.", "red")
            messagebox.showerror("Error", f"Executable '{APP_PATH}' not found. The app folder may be corrupted. Use 'Open Client Folder' to check the path.")
            return

        self.set_status("Launching game...")
        wine_prefix_path = os.path.expanduser(f"~/{WINE_PREFIX_NAME}")
        if not os.path.exists(wine_prefix_path):
            self.set_status("Error: Wine prefix not found. Please run installation first.", "red")
            messagebox.showerror("Error", "Wine prefix not found. Please run the 'Install/Update' option first.")
            return

        os.environ['WINEPREFIX'] = wine_prefix_path
        self.run_command(f"wine \"{APP_PATH}\"", f"Starting the game for {selected_version}")
        self.set_status("Game launched. Check terminal for output.", "blue")

    def show_credits(self):
        credits_window = tk.Toplevel(self)
        credits_window.title("Credits")
        credits_window.geometry("500x400")
        credits_window.resizable(False, False)

        credits_text = tk.Text(credits_window, wrap="word", relief="flat", bd=0, bg=self.cget('bg'))
        credits_text.pack(expand=True, fill="both", padx=20, pady=20)

        credits_content = """
**Archivum Launcher**
Developed and licensed by: Stormwindsky
License: GNU General Public License v3.0

The launcher script is licensed under the GNU GPLv3. All rights to the Roblox platform, its assets, and the client software are reserved by Roblox Corporation.

**Roblox Client Archives**
The Roblox client versions from 2007 to 2009 are sourced from the archives maintained by MaximumADHD. We extend our sincerest gratitude for their invaluable work in preserving these historical clients.
- Roblox 2007: https://github.com/MaximumADHD/Roblox-2007-Client
- Roblox 2008: https://github.com/MaximumADHD/Roblox-2008-Client
- Roblox 2009: https://github.com/MaximumADHD/Roblox-2009-Client

**Tools and Technologies Used**
This launcher would not be possible without the following open-source projects and technologies:
- **Python**: The programming language used to build this application.
- **Tkinter**: The standard GUI toolkit for Python, used to create the user interface.
- **Wine**: The compatibility layer that allows the Roblox clients to run on Linux.
- **Winetricks**: A helper script to install dependencies for Wine applications.
- **subprocess**: Python module to run and manage external commands.
- **urllib.request**: Python module to download the client archives.
- **zipfile**: Python module to extract the compressed client archives.
- **webbrowser**: Python module to open web links in the default browser.
"""

        credits_text.insert("1.0", credits_content)
        credits_text.config(state="disabled") # Make the text read-only
        credits_text.bind("<Button-1>", lambda e: "break") # Block mouse clicks on links

        # Allow selecting and copying text
        credits_text.bind("<Button-1>", lambda e: credits_text.focus_set(), add="+")
        credits_text.bind("<Control-c>", lambda e: credits_text.event_generate("<<Copy>>"), add="+")
        credits_text.bind("<Control-C>", lambda e: credits_text.event_generate("<<Copy>>"), add="+")
        
        # Add a close button
        close_button = ttk.Button(credits_window, text="Close", command=credits_window.destroy)
        close_button.pack(pady=10)

    def open_folder(self):
        selected_version = self.version_var.get()
        if not selected_version:
            messagebox.showerror("Error", "Please select a version.")
            return

        app_folder_name = selected_version.replace(" ", "")
        app_folder = os.path.join(os.path.expanduser("~"), "Archivum-Clients", app_folder_name)
        
        if not os.path.exists(app_folder):
            messagebox.showerror("Error", "Client folder not found. Please run 'Install/Update' first.")
            return
            
        try:
            subprocess.Popen(['xdg-open', app_folder])
            self.set_status("Client folder opened.", "green")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
            self.set_status("Error opening folder.", "red")
            
    # The 'run_camera_fix' function has been completely removed.
    # Its button has also been removed from the create_widgets method.

    def run_installation_thread(self):
        thread = Thread(target=self.install_sequence)
        thread.daemon = True
        thread.start()

    def run_play_thread(self):
        thread = Thread(target=self.run_play)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
