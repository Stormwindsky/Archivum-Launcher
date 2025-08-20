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
        self.geometry("450x450")  # Increased height to accommodate the new button
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
        
        fix_camera_button = ttk.Button(main_frame, text="4. Fix Camera & Mouse", command=self.run_camera_fix)
        fix_camera_button.pack(pady=10, fill="x")

        credits_button = ttk.Button(main_frame, text="5. Credits", command=self.show_credits)
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

        # Intercept for Late 2009 client
        if selected_version == "Late 2009":
            popup = tk.Toplevel(self)
            popup.title("Camera Bug Warning")
            popup.geometry("450x250")
            popup.resizable(False, False)

            message_frame = ttk.Frame(popup, padding="20")
            message_frame.pack(expand=True, fill="both")

            title_label = ttk.Label(message_frame, text="Important Notice", font=("Helvetica", 14, "bold"))
            title_label.pack(pady=10)

            message_text = (
                "The Late 2009 client version is currently affected by a significant camera position bug on Wine. "
                "The creator, Stormwindsky, is actively seeking a solution. If you have any advice or wish to collaborate, "
                "please contact:\n\n"
            )
            message_label = ttk.Label(message_frame, text=message_text, wraplength=400, justify="center")
            message_label.pack(pady=5)

            # Hyperlink to BlueSky
            bluesky_link = tk.Label(message_frame, text="stormwindsky.bsky.social", fg="blue", cursor="hand2")
            bluesky_link.pack()
            bluesky_link.bind("<Button-1>", lambda e: webbrowser.open("https://bsky.app/profile/stormwindsky.bsky.social"))

            # Hyperlink to GameJolt
            gamejolt_link = tk.Label(message_frame, text="https://gamejolt.com/@Stormwindsky", fg="blue", cursor="hand2")
            gamejolt_link.pack()
            gamejolt_link.bind("<Button-1>", lambda e: webbrowser.open("https://gamejolt.com/@Stormwindsky"))

            button_frame = ttk.Frame(message_frame)
            button_frame.pack(pady=20)
            
            # The "Continue Anyway" button
            continue_button = ttk.Button(button_frame, text="Continue Anyway", command=lambda: self.proceed_with_launch(popup))
            continue_button.pack(side="left", padx=10)
            
            # The "Go Back" button
            cancel_button = ttk.Button(button_frame, text="Go Back", command=popup.destroy)
            cancel_button.pack(side="left", padx=10)

            # Wait for the popup to be closed before continuing
            self.wait_window(popup)
            return

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

    def proceed_with_launch(self, popup):
        popup.destroy()
        self.run_play_threaded()

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

    def run_camera_fix(self):
        wine_prefix_path = os.path.expanduser(f"~/{WINE_PREFIX_NAME}")
        if not os.path.exists(wine_prefix_path):
            messagebox.showerror("Error", "Wine prefix not found. Please run 'Install/Update' first.")
            return

        # Check for all fixes
        mwo_check_command = f"WINEPREFIX={wine_prefix_path} wine reg query 'HKEY_CURRENT_USER\Software\Wine\DirectInput' /v MouseWarpOverride"
        dinput_check_command = f"WINEPREFIX={wine_prefix_path} wine reg query 'HKEY_CURRENT_USER\Software\Wine\AppDefaults\RobloxApp.exe\DllOverrides' /v dinput"
        virtualdesktop_check_command = f"WINEPREFIX={wine_prefix_path} wine reg query 'HKEY_CURRENT_USER\Software\Wine\Desktop' /v Default"

        try:
            # Check for mwo fix
            mwo_process = subprocess.run(mwo_check_command, shell=True, capture_output=True, text=True, errors='ignore')
            mwo_applied = "force" in mwo_process.stdout
            
            # Check for dinput fix
            dinput_process = subprocess.run(dinput_check_command, shell=True, capture_output=True, text=True, errors='ignore')
            dinput_applied = "builtin" in dinput_process.stdout or "native,builtin" in dinput_process.stdout

            # Check for virtual desktop
            virtualdesktop_process = subprocess.run(virtualdesktop_check_command, shell=True, capture_output=True, text=True, errors='ignore')
            virtualdesktop_applied = "Desktop" in virtualdesktop_process.stdout and "Default" in virtualdesktop_process.stdout

            if mwo_applied and dinput_applied and virtualdesktop_applied:
                # All fixes are applied, ask user if they want to remove them
                if messagebox.askyesno("Remove Fixes?", "Are you sure you want to remove these fixes? They are designed to improve Roblox's performance on Wine. Note: You will need to manually disable the virtual desktop in winecfg."):
                    # Remove mwo fix
                    mwo_remove_command = f"WINEPREFIX={wine_prefix_path} winetricks mwo=disable"
                    self.run_command(mwo_remove_command, "Removing MouseWarpOverride fix")

                    # Remove dinput override
                    dinput_remove_command = f"WINEPREFIX={wine_prefix_path} wine reg delete 'HKEY_CURRENT_USER\Software\Wine\AppDefaults\RobloxApp.exe\DllOverrides' /v dinput /f"
                    self.run_command(dinput_remove_command, "Removing dinput override")

                    # Inform user about virtual desktop removal
                    messagebox.showinfo("Virtual Desktop", "The fixes have been removed. If you still see a virtual desktop, please run 'winecfg' and disable it from the 'Graphics' tab.")
                else:
                    self.set_status("Operation cancelled.", "orange")
            else:
                # Apply all three fixes
                self.run_command(f"WINEPREFIX={wine_prefix_path} winetricks mwo=force", "Applying MouseWarpOverride fix")
                self.run_command(f"WINEPREFIX={wine_prefix_path} winetricks dinput8", "Applying dinput override fix")

                # Launch winecfg for virtual desktop
                messagebox.showinfo("Virtual Desktop", "Please go to the 'Graphics' tab and enable 'Emulate a virtual desktop' to fix the cursor issue. Choose a suitable resolution (e.g., 1024x768 or 1280x720) then click 'OK'.")
                self.run_command(f"WINEPREFIX={wine_prefix_path} winecfg", "Launching Wine Configuration for Virtual Desktop")

                self.set_status("Camera and mouse fixes applied. Please configure the virtual desktop in the pop-up window.", "green")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to check/apply fixes: {e}")
            self.set_status("Error applying fixes.", "red")
            
    def run_installation_thread(self):
        thread = Thread(target=self.install_sequence)
        thread.daemon = True
        thread.start()

    def run_play_thread(self):
        thread = Thread(target=self.run_play)
        thread.daemon = True
        thread.start()
    
    def run_play_threaded(self):
        # A new function to run the original play logic, to avoid recursion with the popup
        thread = Thread(target=self._launch_game_after_popup)
        thread.daemon = True
        thread.start()

    def _launch_game_after_popup(self):
        selected_version = self.version_var.get()
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

if __name__ == "__main__":
    app = App()
    app.mainloop()