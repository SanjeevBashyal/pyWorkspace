# Google Sheets – Read / Write / Edit operations for Workspace data
import os
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from pyworkspace.Workspace import Workspace
from pyworkspace.Session import Session
from pyworkspace.windows import WindowsScanner, get_current_desktop_guid_str

# ---------------------------------------------------------------------------
# Google Sheets client initialization
# ---------------------------------------------------------------------------
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file("master_credentials.json", scopes=scopes)
    client = gspread.authorize(creds)
    sheet_id = "1Cu2YqjbAeQVNl5N_-bxE6l8_m_iyXOEyBkbf-pd6OKs"
    workbook = client.open_by_key(sheet_id)
except Exception as e:
    workbook = None
    print(f"Error authorizing Google Sheets: {e}")

SEPARATOR = " ||| "

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_worksheet(name: str, rows: int = 200, cols: int = 10):
    """Return the worksheet with the given name, creating it if needed."""
    try:
        return workbook.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Creating new worksheet '{name}'...")
        return workbook.add_worksheet(title=name, rows=str(rows), cols=str(cols))

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# SAVE – scan desktop and write to Sheets
# ---------------------------------------------------------------------------

def save_session_to_sheets(workspace_name: str = "WorkspaceData"):
    """
    Scans all visible programs on the current desktop via WindowsScanner,
    captures their state, and writes them to the Google Sheet.

    Tracks the save in the "Master" sheet, and places the data in the
    named sheet (workspace_name).
    """
    if not workspace_name:
        print("Workspace name cannot be empty.")
        return False

    print(f"Initiating deep scan for workspace '{workspace_name}'...")
    if not workbook:
        print("Google Sheets not initialized. Ensure master_credentials.json is valid.")
        return False

    try:
        # 1. Update the Master Sheet tracking log
        master_sheet = _get_or_create_worksheet("Master")
        master_records = master_sheet.get_all_values()
        if not master_records:
            master_sheet.update("A1", [["Workspace Name", "Desktop Info", "Last Updated"]])
            master_sheet.format("A1:C1", {"textFormat": {"bold": True}})
            master_records = [["Workspace Name", "Desktop Info", "Last Updated"]]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if the workspace is already in the master log
        found = False
        desktop_id_str = get_current_desktop_guid_str()
        
        # Clean the target name to strictly avoid floating whitespace mismatch
        safe_name = workspace_name.strip()
        
        for i, row in enumerate(master_records[0:], start=1):
            if row and row[0].strip() == safe_name:
                master_sheet.update_cell(i, 2, desktop_id_str)
                master_sheet.update_cell(i, 3, timestamp)
                found = True
                break
        
        if not found:
            master_sheet.append_row([safe_name, desktop_id_str, timestamp])

        # 2. Get the specific worksheet for this workspace
        worksheet = _get_or_create_worksheet(workspace_name)
        apps = WindowsScanner.scan()

        headers = ["Program", "Path", "Arguments", "Working Directory",
                    "Window Titles", "Open Files", "Saved At"]

        rows = [headers]
        for app in apps:
            rows.append([
                app["name"],
                app["path"],
                app["args"],
                app["cwd"],
                SEPARATOR.join(app["titles"]),
                SEPARATOR.join(app["open_files"]),
                timestamp,
            ])

        worksheet.clear()
        worksheet.update("A1", rows)
        worksheet.format("A1:G1", {"textFormat": {"bold": True}})

        print(f"Success! {len(apps)} programs saved to '{workspace_name}'.")
        return True

    except Exception as e:
        print(f"Failed to save session to sheets: {e}")
        return False

# ---------------------------------------------------------------------------
# LOAD – read from Sheets and re-launch everything
# ---------------------------------------------------------------------------

def load_session_from_sheets(workspace_name: str = "WorkspaceData"):
    """
    Reads workspace data from Google Sheets and re-launches every program
    with its original arguments, working directory, and individually opens
    each file that was recorded.
    """
    if not workspace_name:
        print("Workspace name cannot be empty.")
        return False

    print(f"Pulling workspace '{workspace_name}' from Google Sheets...")
    if not workbook:
        print("Google Sheets not initialized.")
        return False

    try:
        worksheet = workbook.worksheet(workspace_name)
        records = worksheet.get_all_records()

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

        # Attempt to get the target desktop GUID from the Master sheet
        try:
            master_sheet = workbook.worksheet("Master")
            master_records = master_sheet.get_all_values()
            target_guid_str = ""
            for row in master_records:
                if row and row[0] == workspace_name:
                    if len(row) >= 2:
                        target_guid_str = row[1]
                    break
                    
            if target_guid_str and target_guid_str != "Current Virtual Desktop":
                print(f"Switching to and clearing target desktop GUID: {target_guid_str}")
                from pyworkspace.windows import clear_desktop, switch_to_desktop_by_guid
                switch_to_desktop_by_guid(target_guid_str)
                clear_desktop(target_guid_str)
        except Exception as e:
            print(f"  [Warning] Could not clear and switch desktops context: {e}")

        session = Session(f"cloud_{workspace_name}_session.json")
        session.add_workspace(ws)
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

        print(f"Workspace '{workspace_name}' loaded successfully!")
        return True

    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{workspace_name}' not found.")
        return False
    except Exception as e:
        print(f"Failed to load session from sheets: {e}")
        return False

# ---------------------------------------------------------------------------
# LIST – read names from Master sheet
# ---------------------------------------------------------------------------

def list_workspaces_from_sheets() -> list[str]:
    """
    Reads the 'Master' sheet to return a list of saved workspace names.
    Returns an empty list on failure or if the master sheet is empty.
    """
    if not workbook:
        return []

    try:
        master_sheet = workbook.worksheet("Master")
        names = master_sheet.col_values(1)
        
        # Robust filtering: exclude the header and empty values
        valid_names = [n.strip() for n in names if n.strip() and n.strip() != "Workspace Name"]
        return valid_names

    except gspread.exceptions.WorksheetNotFound:
        return []
    except Exception as e:
        print(f"Failed to list workspaces: {e}")
        return []

# ---------------------------------------------------------------------------
# DELETE – remove workspace and master entry
# ---------------------------------------------------------------------------

def delete_workspace_from_sheets(workspace_name: str) -> bool:
    """
    Deletes the specific named worksheet and removes its entry from the 
    'Master' tracking sheet.
    """
    if not workspace_name:
        return False
        
    print(f"Deleting workspace '{workspace_name}'...")
    if not workbook:
        return False
        
    try:
        # 1. Delete the specific worksheet
        try:
            ws = workbook.worksheet(workspace_name)
            workbook.del_worksheet(ws)
            print(f"  -> Deleted worksheet '{workspace_name}'")
        except gspread.exceptions.WorksheetNotFound:
            print(f"  -> Worksheet '{workspace_name}' already absent.")
            
        # 2. Remove from Master sheet
        try:
            master_sheet = workbook.worksheet("Master")
            records = master_sheet.get_all_values()
            
            # gspread row operations are 1-indexed
            for i, row in enumerate(records, start=1):
                if row and row[0] == workspace_name:
                    master_sheet.delete_rows(i)
                    print(f"  -> Removed '{workspace_name}' from Master.")
                    break
        except gspread.exceptions.WorksheetNotFound:
            pass # Master sheet doesn't exist yet
            
        return True
    except Exception as e:
        print(f"Failed to delete workspace: {e}")
        return False
