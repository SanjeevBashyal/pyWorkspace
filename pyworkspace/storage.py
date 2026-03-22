import os
import sys

def _find_credentials():
    """Check for credentials in PyInstaller bundle first, then cwd."""
    # PyInstaller bundles data files into sys._MEIPASS at runtime
    if getattr(sys, '_MEIPASS', None):
        bundled = os.path.join(sys._MEIPASS, "master_credentials.json")
        if os.path.exists(bundled):
            return bundled
    cwd_path = os.path.join(os.getcwd(), "master_credentials.json")
    if os.path.exists(cwd_path):
        return cwd_path
    return None

CREDENTIALS_PATH = _find_credentials()
USE_CLOUD = CREDENTIALS_PATH is not None

if USE_CLOUD:
    print("Cloud credentials found. Using Google Sheets storage.")
    from pyworkspace.sheets import (
        save_session_to_sheets as save_workspace,
        load_session_from_sheets as load_workspace,
        list_workspaces_from_sheets as list_workspaces,
        delete_workspace_from_sheets as delete_workspace,
        get_workspace_guid_from_sheets as get_workspace_guid
    )
else:
    print("No Cloud credentials found. Using Local JSON storage.")
    from pyworkspace.local_storage import (
        save_session_to_sheets as save_workspace,
        load_session_from_sheets as load_workspace,
        list_workspaces_from_sheets as list_workspaces,
        delete_workspace_from_sheets as delete_workspace,
        get_workspace_guid_from_sheets as get_workspace_guid
    )
