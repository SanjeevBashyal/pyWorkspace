import os
import json
from datetime import datetime
from pyworkspace.Workspace import Workspace
from pyworkspace.Session import Session
from pyworkspace.windows import WindowsScanner, get_current_desktop_guid_str

SEPARATOR = " ||| "
DATA_FILE = os.path.expanduser("~/.pyworkspace_data.json")

def _load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {"master": {}, "workspaces": {}}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"master": {}, "workspaces": {}}

def _save_data(data: dict):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Failed to save local data: {e}")
        return False

def save_session_to_sheets(workspace_name: str = "WorkspaceData"):
    """
    Scans all visible programs on the current desktop via WindowsScanner,
    captures their state, and writes them to the local JSON file.
    Note: function name kept identical for seamless API routing.
    """
    if not workspace_name:
        print("Workspace name cannot be empty.")
        return False

    print(f"Initiating deep scan for workspace '{workspace_name}' (Local)...")
    
    try:
        data = _load_data()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        desktop_id_str = get_current_desktop_guid_str()
        safe_name = workspace_name.strip()

        # Update Master
        data["master"][safe_name] = {
            "desktop_id": desktop_id_str,
            "last_updated": timestamp
        }

        # Update Workspace
        apps = WindowsScanner.scan()
        rows = []
        for app in apps:
            rows.append({
                "Program": app["name"],
                "Path": app["path"],
                "Arguments": app["args"],
                "Working Directory": app["cwd"],
                "Window Titles": SEPARATOR.join(app["titles"]),
                "Open Files": SEPARATOR.join(app["open_files"]),
                "Saved At": timestamp
            })

        data["workspaces"][safe_name] = rows
        _save_data(data)

        print(f"Success! {len(apps)} programs saved locally to '{workspace_name}'.")
        return True
    except Exception as e:
        print(f"Failed to save session to local JSON: {e}")
        return False

def get_workspace_guid_from_sheets(workspace_name: str) -> str:
    if not workspace_name:
        return ""
    try:
        data = _load_data()
        master = data.get("master", {})
        if workspace_name in master:
            return master[workspace_name].get("desktop_id", "")
    except Exception as e:
        print(f"Failed to fetch workspace GUID: {e}")
    return ""

def load_session_from_sheets(workspace_name: str = "WorkspaceData"):
    if not workspace_name:
        print("Workspace name cannot be empty.")
        return False

    print(f"Pulling workspace '{workspace_name}' from Local JSON...")
    
    try:
        data = _load_data()
        records = data.get("workspaces", {}).get(workspace_name)
        
        if not records:
            print(f"No saved workspace entries found in '{workspace_name}'.")
            return False

        ws = Workspace(workspace_name)
        extra_files = []

        for row in records:
            path = str(row.get("Path", "")).strip()
            args = str(row.get("Arguments", "")).strip()
            cwd  = str(row.get("Working Directory", "")).strip()
            open_files_raw = str(row.get("Open Files", "")).strip()

            if not path:
                continue

            ws.add_program(path=path, args=args, cwd=cwd)

            if open_files_raw:
                for f in open_files_raw.split(SEPARATOR):
                    f = f.strip()
                    if f:
                        extra_files.append(f)

        target_guid_str = get_workspace_guid_from_sheets(workspace_name)
        if target_guid_str and target_guid_str != "Current Virtual Desktop":
            try:
                from pyworkspace.windows import clear_desktop
                print(f"Clearing target desktop GUID: {target_guid_str}")
                clear_desktop(target_guid_str)
            except Exception as e:
                print(f"  [Warning] Could not clear target desktop context: {e}")

        session = Session(f"local_{workspace_name}_session.json")
        session.add_workspace(ws)

        def do_launch():
            print(f"Launching programs from '{workspace_name}' workspace...")
            session.open_workspace(workspace_name)
    
            for fpath in extra_files:
                if os.path.isfile(fpath):
                    try:
                        print(f"  -> Opening file: {fpath}")
                        os.startfile(fpath)
                    except Exception as e:
                        print(f"  [Error] Could not open {fpath}: {e}")
                else:
                    print(f"  [Warning] File not found: {fpath}")

        if target_guid_str and target_guid_str != "Current Virtual Desktop":
            from pyworkspace.windows import launch_and_move_to_desktop
            launch_and_move_to_desktop(target_guid_str, do_launch)
        else:
            do_launch()

        print(f"Workspace '{workspace_name}' loaded successfully!")
        return True

    except Exception as e:
        print(f"Failed to load session from local JSON: {e}")
        return False

def list_workspaces_from_sheets() -> list[str]:
    data = _load_data()
    return list(data.get("master", {}).keys())

def delete_workspace_from_sheets(workspace_name: str) -> bool:
    if not workspace_name:
        return False
        
    print(f"Deleting workspace '{workspace_name}' (Local)...")
    try:
        data = _load_data()
        
        if workspace_name in data.get("workspaces", {}):
            del data["workspaces"][workspace_name]
            print(f"  -> Deleted workspace data for '{workspace_name}'")
            
        if workspace_name in data.get("master", {}):
            del data["master"][workspace_name]
            print(f"  -> Removed '{workspace_name}' from Master.")
            
        _save_data(data)
        return True
    except Exception as e:
        print(f"Failed to delete workspace: {e}")
        return False
