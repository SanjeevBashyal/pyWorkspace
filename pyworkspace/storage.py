import os

_CRED_FILE = os.path.join(os.getcwd(), "master_credentials.json")
USE_CLOUD = os.path.exists(_CRED_FILE)

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
