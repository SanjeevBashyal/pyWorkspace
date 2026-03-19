# PyWorkspace

A sleek python package that acts as a Windows workspace and session manager. It allows you to group different files and programs together into a "Workspace" and manage them via a "Session". Executing the class method helps to open certain files/programs together and save them into a session file, allowing you to easily resume work after shutting down your PC.

It also comes with a built-in background service that listens to global shortcut keys (e.g. `Ctrl + Shift + E` to open Explorer).

## Installation

```bash
pip install pyworkspace
```

## Quick Start

### Managing Workspaces Programmatically

```python
from pyworkspace import Workspace, Session

# 1. Initialize a session manager
session = Session("my_daily_session.json")

# 2. Create a Workspace
dev_ws = Workspace("Development")
dev_ws.add_program(r"C:\Windows\System32\cmd.exe")
dev_ws.add_file(r"C:\path\to\your\code.py")

# 3. Add to session and save
session.add_workspace(dev_ws)
session.save()

# 4. Resume
session.resume()
```

### Running the Background Service

Once installed, a console script is automatically generated for you. Run:
```bash
pyworkspace-service
```
This runs the background listener. Optionally, it can be launched via standard hidden `.vbs` scripts for true silent operation on login!

## Requirements
- Python 3.6+
- Windows OS
- `keyboard` library
