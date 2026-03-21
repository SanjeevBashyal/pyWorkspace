import os
import re
import ctypes
from ctypes import wintypes

# Try to import Windows/process APIs
try:
    import win32gui
    import win32process
    import psutil
except ImportError:
    psutil = win32gui = win32process = None
    print("Warning: Missing required libraries for scanning windows (psutil, pywin32)")

# Try to import comtypes for Virtual Desktop filtering
try:
    import comtypes
    from comtypes import GUID as COMGUID

    # COM interface for IVirtualDesktopManager (Windows 10/11)
    CLSID_VirtualDesktopManager = COMGUID("{AA509086-5CA9-4C25-8F95-589D3C07B48A}")
    IID_IVirtualDesktopManager  = COMGUID("{A5CD92FF-29BE-454C-8D04-D82879FB3F1B}")

    class IVirtualDesktopManager(comtypes.IUnknown):
        _iid_ = IID_IVirtualDesktopManager
        _methods_ = [
            comtypes.COMMETHOD(
                [], ctypes.HRESULT, "IsWindowOnCurrentVirtualDesktop",
                (["in"], wintypes.HWND, "topLevelWindow"),
                (["out"], ctypes.POINTER(wintypes.BOOL), "onCurrentDesktop"),
            ),
            comtypes.COMMETHOD(
                [], ctypes.HRESULT, "GetWindowDesktopId",
                (["in"], wintypes.HWND, "topLevelWindow"),
                (["out"], ctypes.POINTER(COMGUID), "desktopId"),
            ),
            comtypes.COMMETHOD(
                [], ctypes.HRESULT, "MoveWindowToDesktop",
                (["in"], wintypes.HWND, "topLevelWindow"),
                (["in"], ctypes.POINTER(COMGUID), "desktopId"),
            ),
        ]

    _HAS_VIRTUAL_DESKTOP = True
except ImportError:
    _HAS_VIRTUAL_DESKTOP = False
    print("Warning: 'comtypes' not installed – virtual desktop filtering disabled.")


def _get_virtual_desktop_manager():
    """Create and return an IVirtualDesktopManager COM instance, or None."""
    if not _HAS_VIRTUAL_DESKTOP:
        return None
    try:
        comtypes.CoInitialize()
        vdm = comtypes.CoCreateInstance(
            CLSID_VirtualDesktopManager,
            interface=IVirtualDesktopManager,
        )
        return vdm
    except Exception:
        return None


def _get_current_desktop_guid(vdm):
    """
    Finds the GUID of the currently active virtual desktop.
    Uses Registry or Foreground Window fallback.
    """
    import winreg
    import uuid
    # 1. Try Windows 11 direct Registry key
    try:
        path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            cur_bytes, _ = winreg.QueryValueEx(key, "CurrentVirtualDesktop")
            return uuid.UUID(bytes_le=cur_bytes)
    except Exception:
        pass

    # 2. Try Windows 10 SessionInfo key
    try:
        import win32process
        session_id = win32process.ProcessIdToSessionId(win32process.GetCurrentProcessId())
        path = rf"Software\Microsoft\Windows\CurrentVersion\Explorer\SessionInfo\{session_id}\VirtualDesktops"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            cur_bytes, _ = winreg.QueryValueEx(key, "CurrentVirtualDesktop")
            return uuid.UUID(bytes_le=cur_bytes)
    except Exception:
        pass

    # 3. Fallback: Get desktop of the currently focused window
    if vdm:
        try:
            import win32gui
            fg_hwnd = win32gui.GetForegroundWindow()
            if fg_hwnd:
                return uuid.UUID(str(vdm.GetWindowDesktopId(fg_hwnd)))
        except Exception:
            pass

    return None


def get_current_desktop_guid_str() -> str:
    """Returns the string representation of the currently active virtual desktop GUID."""
    vdm = _get_virtual_desktop_manager()
    guid = _get_current_desktop_guid(vdm)
    return str(guid) if guid else "Unknown Desktop"


def clear_desktop(target_guid_str: str):
    """Terminates all non-system user applications currently visible on the target desktop."""
    if not _HAS_VIRTUAL_DESKTOP:
        return
        
    import uuid
    import psutil
    import win32process
    try:
        target_guid = uuid.UUID(target_guid_str)
    except Exception:
        return

    vdm = _get_virtual_desktop_manager()
    if not vdm: return

    to_kill_pids = set()

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        try:
            app_guid = uuid.UUID(str(vdm.GetWindowDesktopId(hwnd)))
            if app_guid == target_guid:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                
                try:
                    p = psutil.Process(pid)
                    exe_name = p.name().lower()
                    exe_path = p.exe().lower()
                    # Same safety filters as scanning
                    if exe_name not in WindowsScanner._IGNORED_EXES:
                        if "windowsapps" not in exe_path and "systemapps" not in exe_path:
                            to_kill_pids.add(pid)
                except Exception:
                    pass
        except Exception:
            pass

    win32gui.EnumWindows(callback, None)

    for pid in to_kill_pids:
        try:
            psutil.Process(pid).terminate()
        except Exception as e:
            print(f"Could not kill PID {pid}: {e}")


def switch_to_desktop_by_guid(target_guid_str: str):
    """
    Calculates the registry index position of both the current and target desktops.
    Emits Win+Ctrl+Left/Right strokes to seamlessly drop the user onto it.
    """
    if not _HAS_VIRTUAL_DESKTOP:
        return
        
    import uuid
    import winreg
    import keyboard
    import time
    
    try:
        target_guid = uuid.UUID(target_guid_str)
    except Exception:
        return
        
    vdm = _get_virtual_desktop_manager()
    current_guid = _get_current_desktop_guid(vdm)
    
    if current_guid == target_guid:
        return  # already there
        
    try:
        path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            all_ids, _ = winreg.QueryValueEx(key, "VirtualDesktopIDs")
            
        guids = []
        for i in range(len(all_ids) // 16):
            chunk = all_ids[i*16 : (i+1)*16]
            guids.append(uuid.UUID(bytes_le=chunk))
            
        if current_guid in guids and target_guid in guids:
            cur_idx = guids.index(current_guid)
            tgt_idx = guids.index(target_guid)
            
            diff = tgt_idx - cur_idx
            if diff > 0:
                for _ in range(diff):
                    keyboard.send("win+ctrl+right")
                    time.sleep(0.1)
            elif diff < 0:
                for _ in range(abs(diff)):
                    keyboard.send("win+ctrl+left")
                    time.sleep(0.1)
            
            # Allow time for graphics to settle and desktop focus to be captured natively
            time.sleep(0.5)
    except Exception as e:
        print(f"Desktop switch failed: {e}")


class WindowsScanner:
    """
    Scans the current Windows virtual desktop to detect visible programs,
    their state (arguments, working directory), and any open files.
    Uses three detection strategies for open files:
      1. Command-line arguments
      2. Window title parsing
      3. psutil open_files() with smart document-type filtering
    Only includes windows on the CURRENT virtual desktop.
    """

    # Common file extension pattern for extracting paths from window titles
    _FILE_EXT_PATTERN = re.compile(
        r'[A-Za-z]:\\[^\*\?"<>|:]+\.\w{1,10}',  # absolute Windows path
    )

    # Programs and backgrounds to always ignore
    _IGNORED_EXES = {
        "explorer.exe", "searchhost.exe", "shellexperiencehost.exe",
        "startmenuexperiencehost.exe", "textinputhost.exe",
        "applicationframehost.exe", "systemsettings.exe",
        "runtimebroker.exe", "lockapp.exe", "securityhealthsystray.exe",
        "widgets.exe", "msteams.exe", "gamebar.exe", "powertoys.quickaccess.exe", "nvidia overlay.exe",
    }
    # Extensions considered as user documents / project files
    # (used to filter psutil open_files results)
    _DOCUMENT_EXTENSIONS = {
        # Text / Code
        ".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml", ".toml",
        ".py", ".js", ".ts", ".html", ".css", ".c", ".cpp", ".h", ".java",
        ".cs", ".go", ".rs", ".rb", ".php", ".sh", ".bat", ".ps1", ".sql",
        ".r", ".m", ".ipynb", ".log",
        # Office / Documents
        ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".odt", ".ods", ".odp", ".rtf", ".tex",
        # PDF
        ".pdf",
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".tiff", ".webp",
        ".psd", ".ai", ".eps",
        # CAD / Engineering
        ".dwg", ".dxf", ".dgn", ".rvt", ".skp", ".step", ".stp",
        ".iges", ".igs", ".stl", ".3dm",
        # GIS / Hydraulics
        ".shp", ".geojson", ".kml", ".kmz", ".prj", ".tif",
        ".hdf", ".nc", ".g01", ".g02", ".p01", ".p02",
        # Media
        ".mp3", ".wav", ".mp4", ".avi", ".mkv", ".mov",
        # Archives (often opened by programs)
        ".zip", ".rar", ".7z", ".tar", ".gz",
        # Misc project files
        ".sln", ".csproj", ".vcxproj", ".workspace",
    }

    # Directories that indicate system/internal files (skip them)
    _IGNORED_DIRS = {
        "windows", "program files", "program files (x86)",
        "programdata", "appdata", "$recycle.bin",
        "system volume information",
    }

    @staticmethod
    def _extract_files_from_cmdline(cmdline_parts: list[str]) -> list[str]:
        """Return file paths found in the command-line arguments of a process."""
        files = []
        for arg in cmdline_parts:
            if arg.startswith("-") or arg.startswith("/"):
                continue
            if os.path.isfile(arg):
                files.append(os.path.abspath(arg))
        return files

    @classmethod
    def _extract_file_from_title(cls, title: str) -> str | None:
        """Try to pull a file path out of a window title string."""
        m = cls._FILE_EXT_PATTERN.search(title)
        if m:
            candidate = m.group(0)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
        return None

    @classmethod
    def _extract_open_files_from_handles(cls, process: "psutil.Process") -> list[str]:
        """
        Use psutil's open_files() to get all file handles held by the process,
        then filter to only keep user documents based on extension and path.
        """
        files = []
        try:
            for f in process.open_files():
                path = f.path
                ext = os.path.splitext(path)[1].lower()

                # Only keep files with recognized document extensions
                if ext not in cls._DOCUMENT_EXTENSIONS:
                    continue

                # Skip files inside system directories
                path_lower = path.lower()
                if any(f"\\{d}\\" in path_lower for d in cls._IGNORED_DIRS):
                    continue

                # Skip temp files
                if "\\temp\\" in path_lower or "\\tmp\\" in path_lower:
                    continue

                files.append(os.path.abspath(path))
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            pass
        return files

    @classmethod
    def scan(cls) -> list[dict]:
        """
        Scans all visible windows on the CURRENT virtual desktop only.
        For each unique program it gathers:
          - Executable path, arguments, working directory
          - All window titles belonging to this program
          - Files that the program currently has open
            (detected from command-line args, window titles, AND process file handles)

        Returns:
            A list of dicts, one per unique program.
        """
        if not (win32gui and psutil):
            print("Cannot scan windows without 'psutil' and 'pywin32'.")
            return []

        # Initialize the Virtual Desktop Manager for current-desktop filtering
        vdm = _get_virtual_desktop_manager()
        current_desktop_guid = _get_current_desktop_guid(vdm)

        app_map: dict[str, dict] = {}

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return

            # ── Virtual Desktop filter ──
            if vdm and current_desktop_guid:
                try:
                    import uuid
                    app_guid = uuid.UUID(str(vdm.GetWindowDesktopId(hwnd)))
                    if app_guid != current_desktop_guid:
                        return
                except Exception:
                    pass

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                p = psutil.Process(pid)
                exe_path = p.exe()
                exe_name = p.name().lower()

                if not exe_path:
                    return
                if exe_name in cls._IGNORED_EXES:
                    return
                if "WindowsApps" in exe_path or "SystemApps" in exe_path:
                    return

                cmdline = p.cmdline()
                try:
                    cwd = p.cwd()
                except (psutil.AccessDenied, OSError):
                    cwd = os.path.dirname(exe_path)

                if exe_path not in app_map:
                    app_map[exe_path] = {
                        "name": p.name(),
                        "path": exe_path,
                        "args": " ".join(cmdline[1:]) if len(cmdline) > 1 else "",
                        "cwd": cwd or os.path.dirname(exe_path),
                        "titles": [],
                        "open_files": set(),
                        "_process": p,  # keep reference for file handle scan
                    }
                    # Strategy 1: files from command-line arguments
                    for f in cls._extract_files_from_cmdline(cmdline[1:]):
                        app_map[exe_path]["open_files"].add(f)

                app_map[exe_path]["titles"].append(title)

                # Strategy 2: files from window title
                f = cls._extract_file_from_title(title)
                if f:
                    app_map[exe_path]["open_files"].add(f)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        win32gui.EnumWindows(callback, None)

        # Strategy 3: files from process file handles (run after enumeration)
        for info in app_map.values():
            p = info.pop("_process", None)
            if p:
                for f in cls._extract_open_files_from_handles(p):
                    info["open_files"].add(f)

        results = []
        for info in app_map.values():
            info["open_files"] = sorted(info["open_files"])
            info["titles"] = list(dict.fromkeys(info["titles"]))
            results.append(info)

        return results
