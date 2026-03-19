from pyworkspace.Workspace import Workspace
from pyworkspace.Session import Session

def main():
    # 1. Initialize a session manager
    # This will store the configuration in 'my_daily_session.json'
    session = Session("my_daily_session.json")
    
    # 2. Create a new Workspace
    dev_ws = Workspace("Development")
    
    # 3. Add programs to the workspace
    # Replace these with actual paths on your system
    # Example: dev_ws.add_program(r"C:\Program Files\Notepad++\notepad++.exe")
    # Example with arguments: dev_ws.add_program(r"C:\Windows\System32\cmd.exe", "/k echo Hello Workspace!")
    
    # 4. Add files to the workspace (will open with default Windows application)
    # Example: dev_ws.add_file(r"e:\0_Python\pyWorkspace\code.py")
    
    # 5. Add the workspace to the session
    session.add_workspace(dev_ws)
    
    # 6. Save the session to disk
    session.save()
    
    # ---------------------------------------------------------
    # To resume work later (e.g., after shutting down computer):
    # ---------------------------------------------------------
    
    # 7. You can load and resume everything using:
    # session_to_resume = Session("my_daily_session.json")
    # session_to_resume.resume()
    
    # Or open a specific workspace:
    # session_to_resume.load()
    # session_to_resume.open_workspace("Development")

if __name__ == "__main__":
    main()
