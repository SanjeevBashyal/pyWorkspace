import os
import json
import subprocess
from .Workspace import Workspace

class Session:
    """
    Session helps manage and persist workspaces.
    It can save the current configuration to a JSON file and resume it after a computer shutdown.
    """
    def __init__(self, session_file: str = "session.json"):
        self.session_file = session_file
        self.workspaces = {}

    def add_workspace(self, workspace: Workspace):
        """Add a Workspace object to the current session."""
        self.workspaces[workspace.name] = workspace

    def remove_workspace(self, workspace_name: str):
        """Remove a Workspace from the current session by its name."""
        if workspace_name in self.workspaces:
            del self.workspaces[workspace_name]

    def save(self):
        """Save the session (all managed workspaces) to a JSON file on disk."""
        data = {
            'workspaces': {name: ws.to_dict() for name, ws in self.workspaces.items()}
        }
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"Session successfully saved to {self.session_file}")

    def load(self):
        """Load the session from the JSON file on disk."""
        if not os.path.exists(self.session_file):
            print(f"Session file '{self.session_file}' does not exist. Starting fresh.")
            return

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.workspaces.clear()
            for name, ws_data in data.get('workspaces', {}).items():
                self.workspaces[name] = Workspace.from_dict(ws_data)
            print(f"Session loaded successfully from {self.session_file}")
        except Exception as e:
            print(f"Error loading session from {self.session_file}: {e}")

    def open_workspace(self, workspace_name: str):
        """Launch all programs and files associated with a specific workspace."""
        if workspace_name not in self.workspaces:
            print(f"Workspace '{workspace_name}' not found in the current session.")
            return

        ws = self.workspaces[workspace_name]
        print(f"Opening Workspace: {ws.name}")
        
        # 1. Open all defined programs
        for prog in ws.programs:
            path = prog.get('path')
            args = prog.get('args', '')
            cwd = prog.get('cwd')
            
            if not os.path.exists(path):
                print(f"  [Warning] Program missing: {path}")
                continue
                
            cmd = [path]
            if args:
                cmd.extend(args.split())
                
            try:
                print(f"  -> Starting program: {path}")
                # We use subprocess.Popen to launch asynchronously so it doesn't block the Python script
                subprocess.Popen(cmd, cwd=cwd or os.path.dirname(path))
            except Exception as e:
                print(f"  [Error] Failed to start {path}: {e}")

        # 2. Open all defined files
        for file_item in ws.files:
            file_path = file_item.get('path')
            if not os.path.exists(file_path):
                print(f"  [Warning] File missing: {file_path}")
                continue
                
            try:
                print(f"  -> Opening file: {file_path}")
                # os.startfile is built-in on Windows and behaves like double-clicking a file
                if hasattr(os, 'startfile'):
                    os.startfile(file_path)
                else:
                    # Fallback for non-Windows (just in case, although designed for Windows)
                    subprocess.Popen(['start', '', file_path], shell=True)
            except Exception as e:
                print(f"  [Error] Failed to open {file_path}: {e}")

    def resume(self):
        """Load the session from disk and open all managed workspaces."""
        self.load()
        if not self.workspaces:
            print("No workspaces to resume.")
            return

        for ws_name in self.workspaces:
            self.open_workspace(ws_name)
