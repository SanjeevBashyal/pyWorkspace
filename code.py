from pyworkspace.windows import WindowsScanner
from pyworkspace.Workspace import Workspace
from pyworkspace.Session import Session
from pyworkspace.sheets import save_session_to_sheets

def main():
    # 1. Automatically scan all currently open programs on the desktop
    print("Scanning current desktop...")
    apps = WindowsScanner.scan()
    print(f"Found {len(apps)} programs.\n")

    # 2. Build a Workspace from the live scan
    ws = Workspace("CurrentDesktop")
    for app in apps:
        ws.add_program(path=app["path"], args=app["args"], cwd=app["cwd"])
        for f in app["open_files"]:
            ws.add_file(f)

    # 3. Save as a local JSON session file
    session = Session("current_desktop_session.json")
    session.add_workspace(ws)
    session.save()

    # 4. Also save to Google Sheets
    save_session_to_sheets()

    # 5. Print summary
    for i, app in enumerate(apps, 1):
        print(f"[{i}] {app['name']}")
        print(f"    Path : {app['path']}")
        print(f"    Args : {app['args'] or '(none)'}")
        print(f"    CWD  : {app['cwd']}")
        print(f"    Files: {app['open_files'] or '(none detected)'}")
        print()

    print("Workspace saved to current_desktop_session.json + Google Sheets")
    print("To resume later: session.load() then session.open_workspace('CurrentDesktop')")

if __name__ == "__main__":
    main()
