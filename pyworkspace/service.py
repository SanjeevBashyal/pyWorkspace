import os
import sys
import argparse

def open_explorer():
    """
    Callback function to execute when the hotkey is pressed.
    Opens the default Windows Explorer in the user's visible desktop.
    """
    try:
        os.startfile('explorer.exe')
        print("Explorer opened successfully.")
    except Exception as e:
        print(f"Error opening explorer: {e}")

def run_sheets_save():
    """Scan programs and push to Google Sheets"""
    try:
        from pyworkspace.sheets import save_session_to_sheets
        save_session_to_sheets()
    except Exception as e:
        print(f"Error running sheets save script: {e}")

def run_sheets_load():
    """Pull workspace configurations from Google Sheets and launch"""
    try:
        from pyworkspace.sheets import load_session_from_sheets
        load_session_from_sheets()
    except Exception as e:
        print(f"Error running sheets load script: {e}")

def get_startup_cmd():
    """Builds the background execution command using pythonw"""
    import winreg
    pythonw_path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    
    # We point to the absolute path of this service script so it always finds it
    script_path = os.path.abspath(__file__)
    
    # Encapsulate paths in quotes to account for spaces
    return f'"{pythonw_path}" "{script_path}"'

def install_startup():
    """Adds this script to Windows startup (Current User) via Registry."""
    import winreg
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    command = get_startup_cmd()
    
    try:
        # Open registry key with write access
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as registry_key:
            winreg.SetValueEx(registry_key, "PyWorkspaceService", 0, winreg.REG_SZ, command)
        print("Successfully added PyWorkspace to Windows Startup!")
        print(f"Command configured: {command}")
    except Exception as e:
        print(f"Failed to add to startup: {e}")

def remove_startup():
    """Removes this script from Windows startup."""
    import winreg
    key = winreg.HKEY_CURRENT_USER
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as registry_key:
            winreg.DeleteValue(registry_key, "PyWorkspaceService")
        print("Successfully removed PyWorkspace from Windows Startup.")
    except FileNotFoundError:
        print("PyWorkspace is not cleanly installed in Windows Startup.")
    except Exception as e:
        print(f"Failed to remove from startup: {e}")

def main():
    parser = argparse.ArgumentParser(description="PyWorkspace Background Service")
    parser.add_argument('--install-startup', action='store_true', help='Add the service to Windows startup (Auto-run on login)')
    parser.add_argument('--remove-startup', action='store_true', help='Remove the service from Windows startup')
    args = parser.parse_args()

    # Handle startup registration
    if args.install_startup:
        install_startup()
        sys.exit(0)
    elif args.remove_startup:
        remove_startup()
        sys.exit(0)

    # --- Standard Background Service Loop ---
    try:
        import keyboard
    except ImportError:
        print("The 'keyboard' library is required. Please install it with: pip install keyboard")
        sys.exit(1)

    print("PyWorkspace Service started in background. Listening for hotkeys...")
    
    # Register your desired global hotkeys here
    keyboard.add_hotkey('ctrl+shift+e', open_explorer)
    
    # Register Google Sheets Workspace Sync Operations
    keyboard.add_hotkey('ctrl+shift+s', run_sheets_save)   # Save workspace setup to Sheets
    keyboard.add_hotkey('ctrl+shift+l', run_sheets_load)   # Load workspace setup from Sheets

    # Block indefinitely to keep script alive (quit by pressing Ctrl + Shift + Q)
    keyboard.wait('ctrl+shift+q')
    print("PyWorkspace Service stopped.")

if __name__ == '__main__':
    main()
