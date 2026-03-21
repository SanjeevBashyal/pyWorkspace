import winreg
import uuid
import sys
import ctypes
from comtypes import GUID, IUnknown, COMMETHOD, CoCreateInstance
from ctypes import wintypes

# 1. Define the IVirtualDesktopManager COM Interface
class IVirtualDesktopManager(IUnknown):
    _iid_ = GUID('{a5cd92ff-29be-454c-8d04-d82879fb3f1b}')
    _methods_ = [
        COMMETHOD([], ctypes.HRESULT, 'IsWindowOnCurrentVirtualDesktop',
                  (['in'], wintypes.HWND, 'topLevelWindow'),
                  (['out'], ctypes.POINTER(wintypes.BOOL), 'onCurrent')),
        COMMETHOD([], ctypes.HRESULT, 'GetWindowDesktopId',
                  (['in'], wintypes.HWND, 'topLevelWindow'),
                  (['out'], ctypes.POINTER(GUID), 'desktopId')),
        COMMETHOD([], ctypes.HRESULT, 'MoveWindowToDesktop',
                  (['in'], wintypes.HWND, 'topLevelWindow'),
                  (['in'], ctypes.POINTER(GUID), 'desktopId')),
    ]

def get_desktop_number(app_name):
    import win32gui
    import win32process

    # 2. Find the window handle (HWND) for the app name
    hwnd = None
    def callback(handle, _):
        nonlocal hwnd
        if win32gui.IsWindowVisible(handle):
            _, pid = win32process.GetWindowThreadProcessId(handle)
            try:
                import psutil
                if psutil.Process(pid).name().lower().startswith(app_name.lower()):
                    hwnd = handle
            except:
                pass

    win32gui.EnumWindows(callback, None)
    
    if not hwnd:
        return None

    try:
        # 3. Get the Desktop GUID for the window
        vdm = CoCreateInstance(GUID('{aa509086-5ca9-4c25-8f95-589d3c07b48a}'), IVirtualDesktopManager)
        app_desktop_guid = vdm.GetWindowDesktopId(hwnd)

        # 4. Get all Desktops from the Registry
        path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            all_ids, _ = winreg.QueryValueEx(key, "VirtualDesktopIDs")

        # 5. Match the app's GUID to the registry list
        # Each GUID is 16 bytes long
        for i in range(len(all_ids) // 16):
            chunk = all_ids[i*16 : (i+1)*16]
            # Convert binary chunk to a UUID object for comparison
            if uuid.UUID(bytes_le=chunk) == uuid.UUID(str(app_desktop_guid)):
                return i + 1
    except:
        return 1 # Default to 1 if anything fails (common if only 1 desktop exists)

    return 1

if __name__ == "__main__":
    # Usage: python script.py notepad
    target_app = sys.argv[1] if len(sys.argv) > 1 else "notepad++"
    result = get_desktop_number(target_app)
    if result:
        print(result)